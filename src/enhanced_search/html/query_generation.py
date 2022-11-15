from enhanced_search.annotation import Query

from .sanitzation import get_from_data

# Maps the URL parameter name against the Query objects variables.
request_to_query_mapping = {"query": "original_string"}

# Gives the parameters to sanitize a request parameter
parameter_type_definitions = {
    "query": {
        "name": "query",
        "parameter_type": str,
        "optional": False,
    },
}


def convert_request_data_to_query(request_data: dict) -> Query:
    """Takes a dictionary and returns a Query holding the data.
    Any key in the `request_data` that is not defined internally, will be dropped.

    Raises:
         UserInputException: If a required parameter is not given or if a given
                             parameter value is not of the required type.
    """
    sanitized_query_parameters = {}
    for parameter_name, query_variable in request_to_query_mapping.items():
        parameter_definitions = parameter_type_definitions.get(parameter_name)
        if parameter_definitions is not None:
            sanitized_value = get_from_data(
                request_data, **parameter_definitions
            )

            sanitized_query_parameters[query_variable] = sanitized_value

    return Query(**sanitized_query_parameters)
