import fakeredis
import pytest

from enhanced_search.databases.key_value import RedisDatabase


class TestRedisDatabase:
    def test_read(self, redis):
        """Feature: Read data from Redis."""
        response = redis.read("fagus")
        assert response == "Plant_Flora"

    @pytest.mark.parametrize(
        ["query", "expected_response"],
        [("something:with-colon", "Something with colon")],
    )
    def test_read_with_sanitization(self, query, expected_response, redis):
        response = redis.read(query)
        assert response == expected_response

    @pytest.fixture
    def redis(self, mock_redis_server):
        redis = RedisDatabase(
            url="localhost", port=6379, db_number=1, user="dummy", password="secret"
        )
        redis._db = mock_redis_server
        return redis

    @pytest.fixture
    def mock_redis_server(self, empty_redis_db):
        """A mock Redis instance with some data."""
        empty_redis_db.set(b"fagus", b"Plant_Flora")
        empty_redis_db.set(b"somethingwith-colon", b"Something with colon")

        return empty_redis_db

    @pytest.fixture
    def empty_redis_db(self):
        """Uses Fakeredis to emulate Redis behaviour.
        This instance returns string responses instead of bytes!"""
        db = fakeredis.FakeStrictRedis(version=6, decode_responses=True)
        return db
