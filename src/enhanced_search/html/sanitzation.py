from copy import copy

from typing import Callable, Any


NON_ALPHANUMERIC_CHARACTERS = {
    c for c in map(chr, range(256)) if not c.isalnum() and not c.isspace()
}


def get_from_data(
    data: dict,
    name: str,
    parameter_type: Callable = None,
    optional: bool = False,
    default: Any = None,
    escape_function: Callable = None,
) -> Any:
    """Accesses the parameter with `name` in the `data` and returns its value.
    If the given `name` is NOT present in `data` and `optional` is True, the
    `default` is returned.
    This method does NO sanitizing itself. Only if an `escape_function` is provided
    the data value (and only the value!) is passed to this function for sanitizing
    purposes.
    Raises:
         UserInputException: If a required parameter is not given or if a given
                                parameter value is not of the required type.
    """
    is_name_in_data = name in data

    if not optional and not is_name_in_data:
        raise UserInputException(f"The parameter '{name}' is missing in the request!")

    parameter_value = data.get(name, default)

    if parameter_value is not None and parameter_type is not None:
        try:
            if isinstance(parameter_value, list):
                parameter_value = [parameter_type(value) for value in parameter_value]
            elif parameter_type == bool:
                parameter_value = str(parameter_value).lower() in {
                    "true",
                    "t",
                    "1",
                    "yes",
                }
            else:
                parameter_value = parameter_type(parameter_value)
        except ValueError:
            raise_user_input_exception(
                parameter_name_given_by_user=name, expected_type=parameter_type.__name__
            )

    if escape_function is not None and parameter_value != default:
        parameter_value = escape_function(parameter_value)

    return parameter_value


def sanitize_user_query_string(text: str, escape_quotations: bool = True) -> str:
    """Escapes potential malicious characters in the given text.
    The default behaviour is to escape all non-alphanumeric characters.

    Args:
        text (str): The text to escape.
        escape_quotations (bool): If False, single and double quotations are left
                                  out when escaping. Default: True.
    """
    escape_characters = copy(NON_ALPHANUMERIC_CHARACTERS)
    if not escape_quotations:
        escape_characters.remove('"')
        escape_characters.remove("'")

    return "".join((f"\\{c}" if c in escape_characters else c for c in text))


def raise_user_input_exception(
    parameter_name_given_by_user: str, expected_type: type
) -> None:
    """Raises a UserInputException with the given parameters in the error message."""
    raise UserInputException(
        f'The parameter "{parameter_name_given_by_user}" is expected '
        f"to be of type {expected_type}!"
    )


class UserInputException(Exception):
    """A dedicated exception class for errors that should be returned to the user."""

    pass
