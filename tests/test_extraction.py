from app.services.extractor import ArticleExtractor


def test_article_extractor_prefers_article_content_and_removes_noise() -> None:
    html = """
    <html>
      <body>
        <nav>Navigation</nav>
        <article>
          <p>This is the first important paragraph with enough words to be retained.</p>
          <p>This is the second paragraph with additional reporting details for the summary.</p>
        </article>
        <script>console.log('ignore me');</script>
      </body>
    </html>
    """

    extractor = ArticleExtractor(max_characters=500)
    text = extractor.extract_text(html)

    assert "Navigation" not in text
    assert "ignore me" not in text
    assert "first important paragraph" in text
    assert "second paragraph" in text
