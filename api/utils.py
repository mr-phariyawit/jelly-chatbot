def sanitize_text(text: str) -> str:
    """Remove NUL bytes from string to prevent PostgreSQL errors."""
    if not text:
        return text
    return text.replace('\x00', '')
