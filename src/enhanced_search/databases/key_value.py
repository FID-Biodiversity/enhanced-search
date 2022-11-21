"""Database interfaces to talk to different Key-Value Databases."""

import json
import pathlib
from functools import singledispatchmethod
from typing import Optional, Protocol

from redis import Redis  # type: ignore

from enhanced_search import configuration as config


class KeyValueDatabase(Protocol):
    """An interface class to interact with any Key-Value database.

    Obeys the Database interface.
    """

    def read(self, query: str, *args, **kwargs) -> str:
        """Queries a database with the given query string and
        parameters and returns the retrieved data as string.
        """

    def sanitize_query(self, text: str) -> str:
        """The query for the given database should be sanitized
        as appropriate.
        """


class RedisDatabase:
    """A abstracted connector to Redis.

    Redis is nearly immune against many common attack vectors, but
    some caution should be taken!
    (see https://stackoverflow.com/a/26528595/7504509; CC-BY-SA 3.0).

    Obeys the KeyValueDatabase interface.
    """

    MALICIOUS_CHARACTERS = {":"}

    def __init__(
        self,
        url: str,
        port: int,
        db_number: int,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.url = url
        self.port = port
        self.db_number = db_number
        self.credentials = {}
        self.malicious_characters = self.MALICIOUS_CHARACTERS

        if user is not None:
            self.credentials = {"username": user, "password": password}

        self._db = self._create_redis_connection()

    def read(self, query: str, is_safe: bool = False) -> Optional[str]:
        """Get the associated value for the given query ("key").
        :param query: The key value to look up.
        :param is_safe: If True, no sanitizing will be done. Otherwise,
                potential malicious characters are stripped (Default).
        """
        if not is_safe:
            query = self.sanitize_query(query)

        response = self._db.get(query)

        return response if response is None else response.decode()

    def sanitize_query(self, text: str) -> str:
        """Strips potentially malicious string from the text."""
        for char in self.malicious_characters:
            text = text.replace(char, "")
        return text

    def _create_redis_connection(self) -> Redis:
        parameters = {
            "host": self.url,
            "port": self.port,
            "db": self.db_number,
            "decode_responses": True,  # return strings, instead of bytes
        }

        parameters.update(self.credentials)

        return Redis(**parameters)


class SimpleKeyValueDatabase:
    """A simple wrapper around a dictionary.

    Should NOT be used in production!
    """

    def __init__(self, data: Optional[dict] = None):
        self._db = data if data is not None else {}

    def read(self, query: str, is_safe: bool = False) -> Optional[str]:
        """Get the associated value for the given query ("key").
        :param query: The key value to look up.
        :param is_safe: If True, no sanitizing will be done. Otherwise,
                potential malicious characters are stripped (Default).
        """
        if not is_safe:
            query = self.sanitize_query(query)

        return self._db.get(query)

    def sanitize_query(self, text: str) -> str:
        """In this Database, it does nothing."""
        return text

    @singledispatchmethod
    def parse_data(self, data) -> None:
        """Reads data to the database."""
        raise TypeError(f"The data type of {type(data)} is not supported!")

    @parse_data.register
    def _(self, data: dict) -> None:
        """Reads the data directly into the database."""
        self._db.update(data)

    @parse_data.register
    def _(self, json_data_path: pathlib.Path) -> None:
        """Reads the data from a given json-file into the database."""
        with open(json_data_path, "r", encoding=config.UTF8_STRING) as f:
            data_string = f.read()
            data = json.loads(data_string)

        self.parse_data(data)
