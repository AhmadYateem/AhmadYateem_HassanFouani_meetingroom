"""
Input sanitization utilities for SQL injection and XSS prevention.

Author: Ahmad Yateem
"""

import re
import bleach
from typing import Any, Dict, List, Optional


ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li']
ALLOWED_ATTRIBUTES = {}


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    if not text:
        return text

    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

    return cleaned


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize general string input.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return text

    text = text.replace('\x00', '')

    text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])

    text = text.strip()

    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def sanitize_username(username: str) -> str:
    """
    Sanitize username input.

    Args:
        username: Username to sanitize

    Returns:
        Sanitized username
    """
    if not username:
        return username

    username = re.sub(r'[^a-zA-Z0-9_-]', '', username)

    username = username[:50]

    return username.strip()


def sanitize_email(email: str) -> str:
    """
    Sanitize email input.

    Args:
        email: Email to sanitize

    Returns:
        Sanitized email
    """
    if not email:
        return email

    email = email.strip().lower()

    email = re.sub(r'[^a-z0-9@._+-]', '', email)

    return email


def sanitize_sql_identifier(identifier: str) -> str:
    """
    Sanitize SQL identifiers (table names, column names) to prevent SQL injection.
    Note: This is a backup measure. Always use parameterized queries.

    Args:
        identifier: SQL identifier to sanitize

    Returns:
        Sanitized identifier
    """
    if not identifier:
        return identifier

    identifier = re.sub(r'[^a-zA-Z0-9_]', '', identifier)

    identifier = identifier[:64]

    return identifier


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query to prevent SQL injection in LIKE clauses.

    Args:
        query: Search query to sanitize

    Returns:
        Sanitized query
    """
    if not query:
        return query

    query = query.replace('\\', '\\\\')
    query = query.replace('%', '\\%')
    query = query.replace('_', '\\_')

    query = query.replace('\x00', '')

    query = query.strip()[:200]

    return query


def sanitize_url(url: str) -> str:
    """
    Sanitize URL input.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL
    """
    if not url:
        return url

    url = url.strip()

    if not url.startswith(('http://', 'https://')):
        return ''

    url = re.sub(r'[<>"\']', '', url)

    url = url[:500]

    return url


def sanitize_json_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize JSON input data recursively.

    Args:
        data: Dictionary to sanitize

    Returns:
        Sanitized dictionary
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}

    for key, value in data.items():
        clean_key = sanitize_string(str(key), max_length=100)

        if isinstance(value, str):
            clean_value = sanitize_string(value)
        elif isinstance(value, dict):
            clean_value = sanitize_json_input(value)
        elif isinstance(value, list):
            clean_value = [
                sanitize_json_input(item) if isinstance(item, dict)
                else sanitize_string(str(item)) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            clean_value = value

        sanitized[clean_key] = clean_value

    return sanitized


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    if not filename:
        return filename

    filename = filename.replace('/', '').replace('\\', '').replace('..', '')

    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    filename = filename[:255]

    return filename


def remove_sql_keywords(text: str) -> str:
    """
    Remove common SQL keywords from text to prevent SQL injection.
    Note: This is a backup measure. Always use parameterized queries.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return text

    sql_keywords = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'EXEC', 'EXECUTE', 'UNION', 'JOIN', 'WHERE', 'FROM', 'TABLE',
        'DATABASE', 'COLUMN', 'GRANT', 'REVOKE', 'TRUNCATE', '--', ';',
        'OR 1=1', 'OR 1', 'SCRIPT', 'JAVASCRIPT', 'ONERROR', 'ONLOAD'
    ]

    for keyword in sql_keywords:
        text = re.sub(rf'\b{keyword}\b', '', text, flags=re.IGNORECASE)

    return text


def sanitize_comment(comment: str) -> str:
    """
    Sanitize user comment/review text.

    Args:
        comment: Comment to sanitize

    Returns:
        Sanitized comment
    """
    if not comment:
        return comment

    comment = sanitize_html(comment)

    comment = re.sub(r'\s+', ' ', comment)

    comment = comment[:2000]

    return comment.strip()


def has_sql_injection_pattern(text: str) -> bool:
    """
    Check if text contains potential SQL injection patterns.

    Args:
        text: Text to check

    Returns:
        Boolean indicating if SQL injection pattern detected
    """
    if not text:
        return False

    patterns = [
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"(--|#|/\*|\*/)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(;.*\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b)",
        r"(\bEXEC\b|\bEXECUTE\b)",
        r"('.*OR.*'.*=.*')",
    ]

    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def has_xss_pattern(text: str) -> bool:
    """
    Check if text contains potential XSS patterns.

    Args:
        text: Text to check

    Returns:
        Boolean indicating if XSS pattern detected
    """
    if not text:
        return False

    patterns = [
        r"<script[^>]*>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]

    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False
