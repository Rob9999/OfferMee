from typing import Any, Type, TypeVar, Optional

T = TypeVar("T")


def safe_type(
    value: Any, required_type: Type[T], default_value: T, throw_if_none: bool = False
) -> Optional[T]:
    """
    Will raise on subscripted types like Dict because they are not supported; use dict instead.
    Checks if `value` has the type `required_type`.
    - If `value` is None and throw_if_none == True, an exception is raised.
    - If `value` is None and throw_if_none == False, `default_value` is returned.
    - If `value` is of type `required_type`, `value` is returned.
    - Otherwise, `default_value` is returned.
    """
    if value is None:
        if throw_if_none:
            raise ValueError("Der übergebene Wert ist None")
        return default_value

    if isinstance(value, required_type):
        return value

    return default_value
