import traceback
from typing import Any, List, Type, TypeVar, Optional

from offermee.logger import CentralLogger

T = TypeVar("T")

utils_logger = CentralLogger.getLogger(__name__)


def safe_type(
    value: Any, required_type: Type[T], default_value: T, throw_if_none: bool = False
) -> Optional[T]:
    """
    :param lst: List of items to be converted to a comma-separated string.
    :param default: Default string to return if the list is None or empty.
    :param shall_traceback: Boolean flag to indicate if traceback should be printed on error.
    :return: Comma-separated string of list items or default string on error.
    Will raise on subscripted types like Dict because they are not supported; use dict instead.
    Checks if `value` has the type `required_type`.
    - If `value` is None and throw_if_none == True, an exception is raised.
    - If `value` is None and throw_if_none == False, `default_value` is returned.
    - If `value` is of type `required_type`, `value` is returned.
    - Otherwise, `default_value` is returned.
    """
    if value is None:
        if throw_if_none:
            raise ValueError("The provided value is None")
        return default_value

    if isinstance(value, required_type):
        return value

    return default_value


def to_comma_separated_string(
    lst: Optional[List],
    default: str = "",
    shall_traceback: bool = False,
) -> str:
    """
    Converts a list to a comma-separated string.

    :param lst: The list to be converted to a comma-separated string. If None, the default value is returned.
    :param default: The default string to return if the list is None or an error occurs.
    :param shall_traceback: If True, prints the traceback of any exception that occurs.
    :return: A comma-separated string representation of the list or the default value.
    """
    try:
        return ", ".join(map(str, lst))
    except Exception as error:
        utils_logger.error(
            f"ERROR while transforming to comma separated list string: {error}"
        )
        if shall_traceback:
            traceback.print_exception(type(error), error, error.__traceback__)
        return default
