import json
import os
import time
import uuid
from pathlib import Path

import requests

NEWS_API_URL = "http://localhost:8000/summarize"
COMFYUI_URL = "http://127.0.0.1:8188"
COMFYUI_PROMPT_URL = f"{COMFYUI_URL}/prompt"
COMFYUI_HISTORY_URL = f"{COMFYUI_URL}/history"
COMFYUI_VIEW_URL = f"{COMFYUI_URL}/view"
client_id = str(uuid.uuid4())

# Save the downloaded audio here
OUTPUT_AUDIO_PATH = Path("news_summary_audio.wav")

# Your provided ComfyUI workflow
WORKFLOW_TEMPLATE = {
    "15": {
        "inputs": {
            "audio": "input_voice.wav",
            "audioUI": ""
        },
        "class_type": "LoadAudio",
        "_meta": {
            "title": "LoadAudio"
        }
    },
    "16": {
        "inputs": {
            "filename_prefix": "AutoAudiobook_Segment",
            "audio": [
                "44",
                0
            ]
        },
        "class_type": "SaveAudio",
        "_meta": {
            "title": "Save Audio"
        }
    },
    "44": {
        "inputs": {
            "text": "This is a placeholder text.",
            "model": "VibeVoice-1.5B",
            "attention_type": "auto",
            "quantize_llm": "full precision",
            "free_memory_after_generate": True,
            "diffusion_steps": 20,
            "seed": 0,
            "cfg_scale": 1.3,
            "use_sampling": False,
            "temperature": 0.95,
            "top_p": 0.95,
            "max_words_per_chunk": 250,
            "voice_speed_factor": 1,
            "voice_to_clone": [
                "15",
                0
            ]
        },
        "class_type": "VibeVoiceSingleSpeakerNode",
        "_meta": {
            "title": "VibeVoice Single Speaker"
        }
    }
}


def fetch_news_summary(query: str, max_results: int = 5) -> dict:
    payload = {
        "query": query,
        "max_results": max_results,
    }
    r = requests.post(NEWS_API_URL, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()


def build_narration(news_data: dict) -> str:
    results = news_data.get("results", [])
    lines = []

    lines.append("Here is your news summary.")

    for idx, item in enumerate(results, start=1):
        title = item.get("title", "Untitled article")
        source = item.get("source", "Unknown source")
        summary = item.get("summary")

        # summary may be:
        # - dict with "summary": [...]
        # - list[str]
        # - null
        bullets = []
        if isinstance(summary, dict):
            bullets = summary.get("summary", []) or []
        elif isinstance(summary, list):
            bullets = summary

        if not bullets:
            preview = item.get("content_preview", "").strip()
            if preview:
                bullets = [preview]
            else:
                bullets = ["No summary available for this article."]

        lines.append(f"Story {idx}: {title} from {source}.")
        for bullet in bullets[:4]:
            lines.append(f"- {bullet}")

        lines.append("")

    lines.append("That concludes the news brief.")
    return "\n".join(lines).strip()


def submit_comfyui_workflow(narration_text: str) -> str:
    workflow = json.loads(json.dumps(WORKFLOW_TEMPLATE))  # deep copy
    workflow["44"]["inputs"]["text"] = narration_text

    client_id = str(uuid.uuid4())
    payload = {
        "prompt": workflow,
        "client_id": client_id,
    }

    r = requests.post(COMFYUI_PROMPT_URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()

    prompt_id = data.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI did not return a prompt_id: {data}")
    return prompt_id


def wait_for_audio_result(prompt_id: str, timeout_seconds: int = 600, poll_interval: int = 2) -> dict:
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        r = requests.get(f"{COMFYUI_HISTORY_URL}/{prompt_id}", timeout=30)
        r.raise_for_status()
        history = r.json()

        # ComfyUI history payload usually looks like:
        # { "<prompt_id>": { "outputs": {...} } }
        entry = history.get(prompt_id)
        if entry and entry.get("outputs"):
            return entry

        time.sleep(poll_interval)

    raise TimeoutError(f"Timed out waiting for ComfyUI result for prompt_id={prompt_id}")


def find_audio_files(history_entry: dict) -> list[dict]:
    outputs = history_entry.get("outputs", {})
    audio_files = []

    for node_id, node_output in outputs.items():
        if not isinstance(node_output, dict):
            continue

        # Common ComfyUI structure: node_output["audio"] = [ {filename, subfolder, type}, ... ]
        if "audio" in node_output and isinstance(node_output["audio"], list):
            for item in node_output["audio"]:
                if isinstance(item, dict) and item.get("filename"):
                    audio_files.append(item)

        # Some nodes may expose files under different keys; keep this flexible
        for key in ("gifs", "images", "files"):
            if key in node_output and isinstance(node_output[key], list):
                for item in node_output[key]:
                    if isinstance(item, dict) and item.get("filename"):
                        audio_files.append(item)

    return audio_files


def download_comfyui_file(file_info: dict, dest_path: Path) -> None:
    params = {
        "filename": file_info["filename"],
        "subfolder": file_info.get("subfolder", ""),
        "type": file_info.get("type", "output"),
    }
    r = requests.get(COMFYUI_VIEW_URL, params=params, timeout=60)
    r.raise_for_status()

    dest_path.write_bytes(r.content)


def main():
    query = "Summarize the latest US AI regulation news"

    print("Calling news summarizer...")
    news_data = fetch_news_summary(query=query, max_results=5)

    narration = build_narration(news_data)
    print("\nGenerated narration text:\n")
    print(narration)
    print("\nSubmitting to ComfyUI...")

    prompt_id = submit_comfyui_workflow(narration)
    print(f"Prompt submitted: {prompt_id}")

    history_entry = wait_for_audio_result(prompt_id)
    audio_files = find_audio_files(history_entry)

    if not audio_files:
        raise RuntimeError(f"No audio output found in ComfyUI history for prompt_id={prompt_id}")

    # Download the first audio output
    print("Downloading generated audio...")
    download_comfyui_file(audio_files[0], OUTPUT_AUDIO_PATH)

    print(f"Saved audio to: {OUTPUT_AUDIO_PATH.resolve()}")


if __name__ == "__main__":
    main()
