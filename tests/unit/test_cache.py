"""
Unit tests for cache module.
Tests Redis caching functionality and cache decorators.

Author: Hassan Fouani
"""

import pytest
import json
from unittest.mock import MagicMock, patch

from utils.cache import (
    RedisCache,
    USER_PROFILE_TTL,
    ROOM_AVAILABILITY_TTL,
    ROOM_DETAILS_TTL,
    REVIEW_STATS_TTL
)


class TestRedisCache:
    """Tests for RedisCache class."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client."""
        with patch('utils.cache.redis.Redis') as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def cache(self, mock_redis_client):
        """Create cache instance with mock Redis."""
        with patch('utils.cache.redis.ConnectionPool'):
            return RedisCache(host='localhost', port=6379)

    def test_cache_get_returns_value(self, cache, mock_redis_client):
        """Test getting cached value."""
        mock_redis_client.get.return_value = '{"key": "value"}'
        
        result = cache.get('test_key')
        
        assert result == {"key": "value"}
        mock_redis_client.get.assert_called_once_with('test_key')

    def test_cache_get_returns_none_on_miss(self, cache, mock_redis_client):
        """Test cache miss returns None."""
        mock_redis_client.get.return_value = None
        
        result = cache.get('nonexistent_key')
        
        assert result is None

    def test_cache_set_stores_value(self, cache, mock_redis_client):
        """Test setting cache value."""
        result = cache.set('test_key', {'data': 'value'})
        
        mock_redis_client.setex.assert_called_once()

    def test_cache_set_with_custom_ttl(self, cache, mock_redis_client):
        """Test setting cache value with custom TTL."""
        cache.set('test_key', 'value', ttl=600)
        
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][1] == 600

    def test_cache_delete_removes_key(self, cache, mock_redis_client):
        """Test deleting cache key."""
        cache.delete('test_key')
        
        mock_redis_client.delete.assert_called_once_with('test_key')


class TestCacheSerialization:
    """Tests for cache serialization."""

    @pytest.fixture
    def cache(self):
        """Create cache instance with mock Redis."""
        with patch('utils.cache.redis.Redis'), patch('utils.cache.redis.ConnectionPool'):
            return RedisCache()

    def test_serialize_dict(self, cache):
        """Test serializing dictionary."""
        data = {'key': 'value', 'number': 123}
        result = cache._serialize(data)
        
        assert json.loads(result) == data

    def test_serialize_list(self, cache):
        """Test serializing list."""
        data = [1, 2, 3, 'test']
        result = cache._serialize(data)
        
        assert json.loads(result) == data

    def test_deserialize_json_string(self, cache):
        """Test deserializing JSON string."""
        json_str = '{"key": "value"}'
        result = cache._deserialize(json_str)
        
        assert result == {'key': 'value'}

    def test_deserialize_none(self, cache):
        """Test deserializing None."""
        result = cache._deserialize(None)
        
        assert result is None


class TestCachePatterns:
    """Tests for cache key patterns."""

    def test_user_profile_pattern(self):
        """Test user profile cache pattern."""
        from utils.cache import USER_PROFILE_PATTERN
        
        key = USER_PROFILE_PATTERN.format(user_id=123)
        
        assert key == 'user:123'

    def test_room_details_pattern(self):
        """Test room details cache pattern."""
        from utils.cache import ROOM_DETAILS_PATTERN
        
        key = ROOM_DETAILS_PATTERN.format(room_id=456)
        
        assert key == 'room:456'

    def test_room_availability_pattern(self):
        """Test room availability cache pattern."""
        from utils.cache import ROOM_AVAILABILITY_PATTERN
        
        key = ROOM_AVAILABILITY_PATTERN.format(room_id=1, date='2025-01-15')
        
        assert key == 'room:availability:1:2025-01-15'


class TestCacheTTLs:
    """Tests for cache TTL configurations."""

    def test_user_profile_ttl(self):
        """Test user profile TTL is reasonable."""
        assert USER_PROFILE_TTL == 300
        assert USER_PROFILE_TTL <= 3600

    def test_room_availability_ttl(self):
        """Test room availability TTL is short."""
        assert ROOM_AVAILABILITY_TTL == 60
        assert ROOM_AVAILABILITY_TTL <= 300

    def test_room_details_ttl(self):
        """Test room details TTL is longer."""
        assert ROOM_DETAILS_TTL == 600
        assert ROOM_DETAILS_TTL >= ROOM_AVAILABILITY_TTL

    def test_review_stats_ttl(self):
        """Test review stats TTL."""
        assert REVIEW_STATS_TTL == 300


class TestCacheErrorHandling:
    """Tests for cache error handling."""

    @pytest.fixture
    def cache_with_errors(self):
        """Create cache instance that raises errors."""
        with patch('utils.cache.redis.Redis') as mock, patch('utils.cache.redis.ConnectionPool'):
            client = MagicMock()
            import redis
            client.get.side_effect = redis.RedisError('Connection failed')
            client.setex.side_effect = redis.RedisError('Connection failed')
            mock.return_value = client
            return RedisCache()

    def test_get_handles_redis_error(self, cache_with_errors):
        """Test cache get handles Redis errors gracefully."""
        result = cache_with_errors.get('test_key')
        
        assert result is None

    def test_set_handles_redis_error(self, cache_with_errors):
        """Test cache set handles Redis errors gracefully."""
        result = cache_with_errors.set('test_key', 'value')
        
        assert result is False
