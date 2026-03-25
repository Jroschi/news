from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "News Summarization API"
    ollama_url: str = "http://localhost:11434"   
    ollama_chat_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "mxbai-embed-large"
    searxng_url: str = "http://localhost:8081"
    request_timeout_seconds: float = 20.0
    article_timeout_seconds: float = 15.0
    max_article_characters: int = 12000
    default_search_limit: int = 10

    model_config = SettingsConfigDict(env_prefix="NEWS_", env_file=".env", extra="ignore")


settings = Settings()
