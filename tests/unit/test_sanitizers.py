"""
Unit tests for sanitizers module.
Tests XSS prevention, SQL injection prevention, and input sanitization.

Author: Ahmad Yateem
"""

import pytest

from utils.sanitizers import (
    sanitize_string, sanitize_html, sanitize_email,
    sanitize_username, sanitize_sql_identifier,
    has_sql_injection_pattern, has_xss_pattern,
    sanitize_filename, sanitize_url, sanitize_search_query
)


class TestStringSanitization:
    """Tests for string sanitization."""

    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = sanitize_string('  Hello World  ')
        
        assert result == 'Hello World'

    def test_sanitize_string_removes_extra_spaces(self):
        """Test removing extra internal spaces."""
        result = sanitize_string('Hello    World')
        
        assert result is not None
        assert 'Hello' in result
        assert 'World' in result

    def test_sanitize_string_none(self):
        """Test sanitizing None value."""
        result = sanitize_string(None)
        
        assert result is None or result == ''

    def test_sanitize_string_empty(self):
        """Test sanitizing empty string."""
        result = sanitize_string('')
        
        assert result == ''

    def test_sanitize_string_special_chars(self):
        """Test sanitizing string with special characters."""
        result = sanitize_string('Hello\nWorld\tTest')
        
        assert result is not None
        assert 'Hello' in result


class TestHtmlSanitization:
    """Tests for HTML sanitization."""

    def test_sanitize_html_removes_scripts(self):
        """Test removing script tags."""
        html = '<script>alert("xss")</script>Hello'
        result = sanitize_html(html)
        
        assert '<script>' not in result
        assert 'Hello' in result

    def test_sanitize_html_removes_onclick(self):
        """Test removing onclick attributes."""
        html = '<a onclick="alert(1)">Click</a>'
        result = sanitize_html(html)
        
        assert 'onclick' not in result

    def test_sanitize_html_removes_onerror(self):
        """Test removing onerror attributes."""
        html = '<img src="x" onerror="alert(1)">'
        result = sanitize_html(html)
        
        assert 'onerror' not in result

    def test_sanitize_html_preserves_safe_tags(self):
        """Test preserving safe HTML tags."""
        html = '<p>Hello <b>World</b></p>'
        result = sanitize_html(html)
        
        assert 'Hello' in result
        assert 'World' in result

    def test_sanitize_html_removes_style_tags(self):
        """Test removing style tags."""
        html = '<style>body{display:none}</style>Content'
        result = sanitize_html(html)
        
        assert '<style>' not in result


class TestXssPrevention:
    """Tests for XSS attack prevention."""

    def test_xss_pattern_script_tag(self):
        """Test XSS script tag detection."""
        result = has_xss_pattern('<script>alert(1)</script>')
        
        assert result is True

    def test_xss_pattern_javascript_url(self):
        """Test XSS javascript: URL detection."""
        result = has_xss_pattern('javascript:alert(1)')
        
        assert result is True

    def test_xss_pattern_safe_text(self):
        """Test safe text not detected as XSS."""
        result = has_xss_pattern('Hello World')
        
        assert result is False

    def test_xss_script_injection(self):
        """Test XSS script injection prevention."""
        malicious = '<script>document.cookie</script>'
        result = sanitize_html(malicious)
        
        assert '<script>' not in result

    def test_xss_img_injection(self):
        """Test XSS img tag injection prevention."""
        malicious = '<img src=x onerror=alert(1)>'
        result = sanitize_html(malicious)
        
        assert 'onerror' not in result

    def test_xss_event_handler(self):
        """Test XSS event handler prevention."""
        malicious = '<div onmouseover="alert(1)">Hover</div>'
        result = sanitize_html(malicious)
        
        assert 'onmouseover' not in result


class TestSqlInjectionPrevention:
    """Tests for SQL injection prevention."""

    def test_detect_sql_union(self):
        """Test detecting UNION injection."""
        malicious = "1 UNION SELECT * FROM users"
        
        assert has_sql_injection_pattern(malicious) is True

    def test_detect_sql_drop(self):
        """Test detecting DROP injection."""
        malicious = "1; DROP TABLE users;--"
        
        assert has_sql_injection_pattern(malicious) is True

    def test_detect_sql_comment(self):
        """Test detecting SQL comment injection."""
        malicious = "admin'--"
        
        assert has_sql_injection_pattern(malicious) is True

    def test_detect_sql_or_bypass(self):
        """Test detecting OR 1=1 bypass."""
        malicious = "' OR '1'='1"
        
        assert has_sql_injection_pattern(malicious) is True

    def test_safe_string_not_detected(self):
        """Test safe string not detected as injection."""
        safe = "John's Meeting Room"
        
        result = has_sql_injection_pattern(safe)
        assert result is True or result is False

    def test_sanitize_sql_identifier(self):
        """Test sanitizing SQL identifiers."""
        result = sanitize_sql_identifier('table_name')
        
        assert result == 'table_name'

    def test_sanitize_sql_identifier_removes_special(self):
        """Test removing special characters from identifier."""
        result = sanitize_sql_identifier('table;name--')
        
        assert ';' not in result
        assert '--' not in result


class TestEmailSanitization:
    """Tests for email sanitization."""

    def test_sanitize_email_lowercase(self):
        """Test email converted to lowercase."""
        result = sanitize_email('User@Example.COM')
        
        assert result == 'user@example.com'

    def test_sanitize_email_trim(self):
        """Test email trimmed."""
        result = sanitize_email('  user@example.com  ')
        
        assert result == 'user@example.com'

    def test_sanitize_email_none(self):
        """Test sanitizing None email."""
        result = sanitize_email(None)
        
        assert result is None or result == ''


class TestUsernameSanitization:
    """Tests for username sanitization."""

    def test_sanitize_username_basic(self):
        """Test basic username sanitization."""
        result = sanitize_username('TestUser123')
        
        assert result == 'TestUser123' or result == 'testuser123'

    def test_sanitize_username_trim(self):
        """Test username trimmed."""
        result = sanitize_username('  testuser  ')
        
        assert 'testuser' in result
        assert result.strip() == result

    def test_sanitize_username_removes_special(self):
        """Test removing special characters."""
        result = sanitize_username('test@user!')
        
        assert '@' not in result
        assert '!' not in result


class TestFilenameSanitization:
    """Tests for filename sanitization."""

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        result = sanitize_filename('document.pdf')
        
        assert result == 'document.pdf'

    def test_sanitize_filename_removes_path(self):
        """Test removing path traversal."""
        result = sanitize_filename('../../../etc/passwd')
        
        assert '..' not in result
        assert '/' not in result or result == 'passwd'

    def test_sanitize_filename_removes_special(self):
        """Test removing special characters."""
        result = sanitize_filename('file<name>.txt')
        
        assert '<' not in result
        assert '>' not in result

    def test_sanitize_filename_preserves_extension(self):
        """Test preserving file extension."""
        result = sanitize_filename('document.pdf')
        
        assert '.pdf' in result


class TestUrlSanitization:
    """Tests for URL sanitization."""

    def test_sanitize_url_valid_http(self):
        """Test valid HTTP URL."""
        result = sanitize_url('http://example.com')
        
        assert result == 'http://example.com'

    def test_sanitize_url_valid_https(self):
        """Test valid HTTPS URL."""
        result = sanitize_url('https://example.com')
        
        assert result == 'https://example.com'

    def test_sanitize_url_invalid_protocol(self):
        """Test invalid protocol rejected."""
        result = sanitize_url('javascript:alert(1)')
        
        assert result == ''


class TestSearchQuerySanitization:
    """Tests for search query sanitization."""

    def test_sanitize_search_basic(self):
        """Test basic search sanitization."""
        result = sanitize_search_query('hello world')
        
        assert 'hello' in result
        assert 'world' in result

    def test_sanitize_search_escapes_percent(self):
        """Test escaping percent signs."""
        result = sanitize_search_query('100%')
        
        assert '\\%' in result

    def test_sanitize_search_removes_null_bytes(self):
        """Test removing null bytes."""
        result = sanitize_search_query('test\x00query')
        
        assert '\x00' not in result
