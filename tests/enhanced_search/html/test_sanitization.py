from typing import Iterable, Type

import pytest

from enhanced_search.html.sanitzation import (
    UserInputException,
    get_from_data,
    sanitize_user_query_string,
)

GET_STRING = "GET"
POST_STRING = "POST"


def dummy_escape_function(term: str) -> str:
    return term.replace("\\", "\\\\").replace("$", "\\$")


class TestDataExtractionFromRequest:
    @pytest.mark.parametrize(
        ["request_data", "function_parameters", "expected_values"],
        [
            # Scenario - Required parameter
            (
                {"format": "json"},
                ({"name": "format", "parameter_type": str, "optional": False},),
                ("json",),
            ),
            # Scenario - Optional parameter not given, but type checked
            (
                {},
                (
                    {
                        "name": "radius",
                        "parameter_type": int,
                        "optional": True,
                        "default": None,
                    },
                ),
                (None,),
            ),
            # Scenario - Required and optional parameters, both given
            (
                {
                    "term": "https://www.biofid.de/ontologies/Tracheophyta/gbif/1234",
                    "format": "json",
                },
                (
                    {"name": "format", "parameter_type": str, "optional": False},
                    {"name": "term", "parameter_type": str, "optional": True},
                ),
                ("json", "https://www.biofid.de/ontologies/Tracheophyta/gbif/1234"),
            ),
            # Scenario - Required and optional parameters, only required given
            (
                {
                    "format": "json",
                },
                (
                    {"name": "format", "parameter_type": str, "optional": False},
                    {
                        "name": "term",
                        "parameter_type": str,
                        "optional": True,
                        "default": "*:*",
                    },
                ),
                ("json", "*:*"),
            ),
            # Scenario - Mixed parameter types
            (
                {
                    "term": "https://www.biofid.de/ontologies/Tracheophyta/gbif/1234",
                    "format": "json",
                    "radius": 10,
                    "lon": 50.1,
                    "lat": 8.6,
                },
                (
                    {"name": "format", "parameter_type": str, "optional": False},
                    {
                        "name": "term",
                        "parameter_type": str,
                        "optional": True,
                        "default": "*:*",
                    },
                    {"name": "radius", "parameter_type": int, "optional": True},
                    {"name": "lon", "parameter_type": float, "optional": True},
                    {"name": "lat", "parameter_type": float, "optional": True},
                ),
                (
                    "json",
                    "https://www.biofid.de/ontologies/Tracheophyta/gbif/1234",
                    10,
                    50.1,
                    8.6,
                ),
            ),
            # Scenario - Parameter is list
            (
                {"numbers": [1, 2, 3]},
                (
                    {
                        "name": "numbers",
                        "parameter_type": float,
                        "optional": False,
                    },
                ),
                ([1.0, 2.0, 3.0],),
            ),
            # Scenario - Parameter includes boolean
            (
                {"isTrue": True, "isFalse": False},
                (
                    {
                        "name": "isTrue",
                        "parameter_type": bool,
                        "optional": False,
                    },
                    {
                        "name": "isFalse",
                        "parameter_type": bool,
                        "optional": False,
                    },
                ),
                (True, False),
            ),
            # Scenario - Escape function given
            (
                {"term": "Some \\ string with intere$ting ch4racters!"},
                ({"name": "term", "escape_function": dummy_escape_function},),
                ("Some \\\\ string with intere\\$ting ch4racters!",),
            ),
            # Scenario - Do not escape default values
            (
                {},
                (
                    {
                        "name": "term",
                        "optional": True,
                        "default": "$$$",
                        "escape_function": dummy_escape_function,
                    },
                ),
                ("$$$",),
            ),
        ],
    )
    def test_get_from_data_for_valid_data(
        self, request_data: dict, function_parameters: dict, expected_values: Exception
    ):
        assert_value_extraction_with_get_from_data(
            request_data, function_parameters, expected_values
        )

    @pytest.mark.parametrize(
        ["request_data", "function_parameters", "expected_exception"],
        [
            (  # Scenario - Mandatory parameter "term" is missing
                {"radius": "test"},
                ({"name": "term", "parameter_type": str, "optional": False},),
                UserInputException,
            ),
            (  # Scenario - Given parameter value is not of the expected type
                {"radius": "test"},
                ({"name": "radius", "parameter_type": int, "optional": False},),
                UserInputException,
            ),
        ],
    )
    def test_get_from_data_for_invalid_data(
        self,
        request_data: dict,
        function_parameters: dict,
        expected_exception: Type[Exception],
    ):
        irrelevant_dummy_list = [None]

        with pytest.raises(expected_exception):
            assert_value_extraction_with_get_from_data(
                request_data, function_parameters, irrelevant_dummy_list
            )


class TestStringEscaping:
    @pytest.mark.parametrize(
        ["text", "expected_output"],
        [
            ("Das ist ein Test", "Das ist ein Test"),
            ("Das ist ein Test!", "Das ist ein Test\\!"),
            (
                "H3r& #r3 $ome '}haracters' \"for\" %escaping",
                "H3r\\& \\#r3 \\$ome \\'\\}haracters\\' \\\"for\\\" \\%escaping",
            ),
        ],
    )
    def test_sanitize_user_query_string_default(self, text, expected_output):
        escaped_text = sanitize_user_query_string(text)
        assert escaped_text == expected_output

    @pytest.mark.parametrize(
        ["text", "expected_output"],
        [
            ("Das ist ein Test", "Das ist ein Test"),
            ("Das ist ein Test!", "Das ist ein Test\\!"),
            (
                "H3r& #r3 $ome '}haracters' \"for\" %escaping",
                "H3r\\& \\#r3 \\$ome '\\}haracters' \"for\" \\%escaping",
            ),
        ],
    )
    def test_sanitize_user_query_string_no_quotation_escaping(
        self, text, expected_output
    ):
        escaped_text = sanitize_user_query_string(text, escape_quotations=False)
        assert escaped_text == expected_output


def assert_value_extraction_with_get_from_data(
    request_data, function_parameters: Iterable, expected_values
):
    for parameters, value in zip(function_parameters, expected_values):
        assert get_from_data(request_data, **parameters) == value
