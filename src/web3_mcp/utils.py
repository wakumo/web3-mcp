"""
Utility functions for web3-mcp
"""

import inspect
from enum import Enum
from typing import Any, Optional, Set, Tuple

from .constants import MAX_PAGE_SIZE, NEXT_PAGE_TOKEN_ATTRS


def to_serializable(
    obj: Any, visited: Optional[Set[int]] = None, max_depth: int = 10, current_depth: int = 0
) -> Any:
    """
    Recursively convert object to JSON-serializable format with cycle detection.

    Args:
        obj: Object to serialize
        visited: Set of object IDs already visited (for cycle detection)
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth

    Returns:
        JSON-serializable representation of the object
    """
    if visited is None:
        visited = set()

    # Prevent infinite recursion
    if current_depth > max_depth:
        return str(obj)

    # Handle circular references
    obj_id = id(obj)
    if obj_id in visited:
        return "<circular reference>"

    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, Enum):
        # Handle Enum objects - just return the value
        return obj.value if hasattr(obj, "value") else str(obj)
    elif isinstance(obj, dict):
        visited.add(obj_id)
        try:
            result = {k: to_serializable(v, visited, max_depth, current_depth + 1) for k, v in obj.items()}
        finally:
            visited.discard(obj_id)
        return result
    elif isinstance(obj, (list, tuple)):
        visited.add(obj_id)
        try:
            result = [to_serializable(item, visited, max_depth, current_depth + 1) for item in obj]
        finally:
            visited.discard(obj_id)
        return result
    elif hasattr(obj, "__dict__"):
        visited.add(obj_id)
        try:
            # Filter out internal/private attributes
            filtered_dict = {
                k: to_serializable(v, visited, max_depth, current_depth + 1)
                for k, v in obj.__dict__.items()
                if not k.startswith("_") or k == "_value_"  # Keep _value_ for enums
            }
            # If it's an enum-like object with _value_, use that
            if "_value_" in filtered_dict and len(filtered_dict) == 1:
                return filtered_dict["_value_"]
            return filtered_dict
        finally:
            visited.discard(obj_id)
    else:
        return str(obj)


def get_next_page_token(result: Any) -> str:
    """
    Extract next page token from result object.

    Args:
        result: Result object that may contain pagination token

    Returns:
        Next page token as string, empty string if not found
    """
    if result is None:
        return ""

    # Try to get from attributes
    for attr_name in NEXT_PAGE_TOKEN_ATTRS:
        token = getattr(result, attr_name, None)
        if token:
            return str(token)

    # Try to get from dict
    if isinstance(result, dict):
        for attr_name in NEXT_PAGE_TOKEN_ATTRS:
            token = result.get(attr_name)
            if token:
                return str(token)

    return ""


def convert_iterable_to_list(
    items: Any, max_items: Optional[int] = None, default_max: int = MAX_PAGE_SIZE
) -> list:
    """
    Safely convert an iterable to a list with optional limit.

    Args:
        items: Iterable to convert
        max_items: Maximum number of items to include (None = use default_max)
        default_max: Default maximum if max_items is None

    Returns:
        List of items, empty list on error
    """
    if items is None:
        return []

    if not hasattr(items, "__iter__") or isinstance(items, (str, bytes)):
        return [items] if items else []

    limit = max_items if max_items is not None else default_max
    result = []
    try:
        for i, item in enumerate(items):
            result.append(item)
            if i >= limit - 1:
                break
    except Exception:
        return []

    return result


def extract_paginated_result(
    result: Any,
    items_attr: str,
    page_size: Optional[int] = None,
    default_max: int = MAX_PAGE_SIZE,
    alternative_keys: Optional[list[str]] = None,
) -> Tuple[Optional[str], list]:
    """
    Extract paginated items and next page token from Ankr API result.

    Handles various result formats:
    - Response object with items attribute (e.g., result.assets, result.holders)
    - Iterable (list, generator)
    - Dict with items key
    - Single object

    Args:
        result: API result object
        items_attr: Name of attribute containing items (e.g., "assets", "holders")
        page_size: Maximum number of items to return
        default_max: Default maximum if page_size is None
        alternative_keys: Alternative keys to try if items_attr not found in dict

    Returns:
        Tuple of (next_page_token, items_list)
    """
    if result is None:
        return None, []

    # Check if it's an async generator (cannot process synchronously)
    if inspect.isasyncgen(result):
        return None, []

    # If result has items attribute (response object)
    if hasattr(result, items_attr):
        items = getattr(result, items_attr, None) or []
        next_token = get_next_page_token(result)
        items_list = convert_iterable_to_list(items, page_size, default_max)
        return next_token, items_list

    # If result is iterable (generator/list)
    if hasattr(result, "__iter__") and not isinstance(result, (str, bytes, dict)):
        items_list = convert_iterable_to_list(result, page_size, default_max)
        return None, items_list

    # If result is a dict
    if isinstance(result, dict):
        # Try items_attr first, then alternative keys, then common alternatives
        items = result.get(items_attr)
        if items is None and alternative_keys:
            for key in alternative_keys:
                items = result.get(key)
                if items is not None:
                    break
        if items is None:
            items = result.get("items") or []
        next_token = get_next_page_token(result)
        items_list = convert_iterable_to_list(items, page_size, default_max)
        return next_token, items_list

    # Single object - wrap in list
    return None, [result]
