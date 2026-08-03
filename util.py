from html import escape


def esc(text):
    """Escape user-provided text so it can't break Telegram's HTML parse mode."""
    if text is None:
        return ""
    return escape(str(text))
