import json
import os
import re
from typing import Any, Dict, List, Tuple, Union


class Container:
    """
    Wraps a dict-based container. Supports dotted+bracketed paths (e.g. "foo.bar[2].baz")
    with automatic creation of intermediate dicts/lists as needed.
    """

    Token = Tuple[str, List[Union[int, slice]]]  # (base_key, [ops])

    def __init__(self, name: str = None, data: Dict[str, Any] = None):
        """
        :param name: Optional name for the container
        :param data: The initial dictionary to wrap
        """
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise TypeError("Container must wrap a dictionary at the top level.")
        self._name = name
        self._data = data

    # -------------------------------------------------------------------------
    #  Public API
    # -------------------------------------------------------------------------

    def get_name(self):
        return self._name

    def data(self) -> Dict[str, Any]:
        """Return the underlying dictionary."""
        return self._data

    def dump(self, path: str = None, file_name: str = None, indent: int = 2) -> bool:
        """Dump the container to a JSON file at `path` with `file_name` and `indent` level.

        Args:
            path (str, optional): _description_. Defaults to None. If none the user path is used.
            file_name (str, optional): _description_. Defaults to None. If None the container name is used.
            indent (int, optional): _description_. Defaults to 2.

        Returns:
            bool: _description_
        """
        if path is None:
            # get user path
            path = os.path.join(os.path.expanduser("~"), "offerme_data")
        if file_name is None:
            # get container name as file name
            file_name = self._name
        try:
            path_name = os.path.join(path, file_name)
            if not os.path.exists(path):
                os.makedirs(path)
            with open(path_name, "w") as f:
                json.dump(self._data, f, indent=indent)
            return True
        except Exception as e:
            print(f"Error dumping container '{self._name}' to '{path_name}': {e}")
            return False

    def dumps(self, indent: int = 2) -> str:
        """Return a pretty-printed JSON representation of the container."""
        return json.dumps(self._data, indent=indent)

    def set_value(self, path_name: str, value: Any) -> None:
        """
        Set the value at `path_name`, creating intermediate structures as needed.

        Examples:
          c.set_value("abc", 123)                              # => c._data["abc"] = 123
          c.set_value("abc.def[2].ghi", "X")                   # => c._data["abc"]["def"][2]["ghi"] = "X"
          c.set_value("abc.def[2].ghi[5]", 999)                # => c._data["abc"]["def"][2]["ghi"][5] = 999
          c.set_value("abc[0].def", 456)                       # => c._data["abc"][0]["def"] = 456
          c.set_value("abc.foo", {"nested": "object"})         # => c._data["abc"]["foo"] = {...}
        """
        if not path_name:
            raise ValueError("Missing path name.")
        tokens = self._parse_path(path_name)
        if not tokens:
            raise ValueError("Path has no tokens (empty).")

        # Walk the tokens, forcing creation/overwriting as we go.
        current_obj = self._data
        parent_obj = None
        parent_key = None

        # We'll go through all tokens. For each token, we handle:
        #  (1) base_key => dict-step
        #  (2) array_ops => list-step(s)

        # For all but the last token, we do "full" navigation.
        # For the final token, we do the same but then do the "final assignment".
        for i, (base_key, array_ops) in enumerate(tokens):
            is_last_token = i == len(tokens) - 1

            # 1) Dictionary-step if base_key is not empty
            if base_key:
                if not isinstance(current_obj, dict):
                    # We want a dict here, so forcibly replace whatever is in the parent's slot
                    if parent_obj is not None:
                        # Overwrite the parent's child with a new dict
                        new_dict = {}
                        _store_in_parent(parent_obj, parent_key, new_dict)
                        current_obj = new_dict
                    else:
                        # top-level is not a dict => forcibly set to {}
                        self._data = {}
                        current_obj = self._data

                # Now current_obj must be a dict. If the key doesn't exist or is the wrong type, it's overwritten below
                if base_key not in current_obj or not isinstance(
                    current_obj[base_key], (dict, list)
                ):
                    # Just create an empty dict, in case the next steps are array ops
                    current_obj[base_key] = {}
                parent_obj = current_obj
                parent_key = base_key
                current_obj = current_obj[base_key]

            # 2) If there are array operations, ensure we have a list at each step
            for j, op in enumerate(array_ops):
                # We might also do partial array ops if not the last. But let's do them all normally.
                # Make sure current_obj is a list
                if not isinstance(current_obj, list):
                    # Overwrite it with a list in the parent's container
                    new_list = []
                    _store_in_parent(parent_obj, parent_key, new_list)
                    current_obj = new_list

                # Then handle the indexing
                if isinstance(op, slice):
                    # Slicing returns a sub-list. We do not expand automatically.
                    current_obj = current_obj[op]
                    # If the user does something like "abc[2:5][1]", it's quite tricky to keep indexing deeper.
                    # For simplicity, we do not fill slices if they are out-of-range.
                    # If you want more robust slice behavior, you can implement it.
                else:
                    # Single index
                    idx = op
                    if idx < 0:
                        idx += len(current_obj)
                    # Expand list if needed
                    if idx >= len(current_obj):
                        current_obj.extend([None] * (idx - len(current_obj) + 1))
                    # If there's nothing at that slot, create an empty dict so we can keep going
                    if current_obj[idx] is None:
                        current_obj[idx] = {}
                    parent_obj = current_obj
                    parent_key = idx
                    current_obj = current_obj[idx]

            if is_last_token:
                # If we're at the very last token, we do the actual assignment of `value`.
                # BUT only if there's no array_ops => we do dict assignment
                # or if there *are* array_ops => we do "overwrite" at the final slot.
                if array_ops:
                    # array_ops => we've ended up "inside" the final slot if there's still a final object
                    # That means `current_obj` is the final sub-dict or sub-list. We just need to do a final overwrite.
                    # BUT the code above has already "stepped in". So all we do is parent_obj[parent_key] = value
                    _store_in_parent(parent_obj, parent_key, value)
                else:
                    # no array ops => that means we want parent_obj[base_key] = value
                    # but note we are "inside" current_obj. We want to store the `value` in the parent's child
                    _store_in_parent(parent_obj, parent_key, value)
            # else: we move on to the next token

    def get_value(self, path_name: str, default: Any = None) -> Any:
        """
        Retrieve the value at `path_name`. Returns `default` if the path is missing or invalid.
        Example:
          c.get_value("abc") -> whatever is in c._data["abc"]
          c.get_value("abc.def[2].ghi") -> deeper fetch
        """
        if not path_name:
            raise ValueError("Missing path name.")
        tokens = self._parse_path(path_name)
        if not tokens:
            print(f"Path has no tokens (empty): {path_name}")
            return default

        current_obj = self._data
        for base_key, array_ops in tokens:
            # Dictionary step
            if base_key:
                if not isinstance(current_obj, dict):
                    print(f"Path invalid: {path_name}")
                    return default  # path invalid
                if base_key not in current_obj:
                    print(f"Key not found: {base_key}")
                    return default
                current_obj = current_obj[base_key]
                # print(f"current_obj: {current_obj}")

            # Array-ops
            for op in array_ops:
                if not isinstance(current_obj, list):
                    return default
                if isinstance(op, slice):
                    try:
                        current_obj = current_obj[op]
                    except Exception:
                        return default
                else:
                    idx = op
                    if idx < 0:
                        idx += len(current_obj)
                    if idx < 0 or idx >= len(current_obj):
                        return default
                    if current_obj[idx] is None:
                        return default
                    current_obj = current_obj[idx]

        return current_obj

    def del_entry(self, path_name: str) -> None:
        """
        Delete an entry at `path_name` from the container, if it exists.
        Example:
          del_entry("abc.def[2].ghi") => del self._data["abc"]["def"][2]["ghi"]
        """
        if not path_name:
            raise ValueError("Missing path name.")
        tokens = self._parse_path(path_name)
        if not tokens:
            return

        # We only need to navigate to the *parent* of the final step
        # and then do the final deletion from that parent.
        # So let's process all but the last token fully,
        # then interpret the final token carefully.
        parent_obj = self._data
        for base_key, array_ops in tokens[:-1]:
            # Dictionary step
            if base_key:
                if not isinstance(parent_obj, dict):
                    return
                if base_key not in parent_obj:
                    return
                parent_obj = parent_obj[base_key]

            # array-ops
            for op in array_ops:
                if not isinstance(parent_obj, list):
                    return
                if isinstance(op, slice):
                    try:
                        parent_obj = parent_obj[op]
                    except:
                        return
                else:
                    idx = op
                    if idx < 0:
                        idx += len(parent_obj)
                    if idx < 0 or idx >= len(parent_obj):
                        return
                    if parent_obj[idx] is None:
                        return
                    parent_obj = parent_obj[idx]

        # Now handle the final token
        final_key, final_ops = tokens[-1]
        # 1) If there's a final_key, step in
        if final_key:
            if not isinstance(parent_obj, dict):
                return
            if final_key not in parent_obj:
                return
            parent_obj = parent_obj[final_key]

        # 2) If there are array ops, we do the last array op as a deletion
        if final_ops:
            # Navigate all but the last array op
            for op in final_ops[:-1]:
                if not isinstance(parent_obj, list):
                    return
                if isinstance(op, slice):
                    try:
                        parent_obj = parent_obj[op]
                    except:
                        return
                else:
                    idx = op
                    if idx < 0:
                        idx += len(parent_obj)
                    if idx < 0 or idx >= len(parent_obj):
                        return
                    if parent_obj[idx] is None:
                        return
                    parent_obj = parent_obj[idx]

            # final op => del
            last_op = final_ops[-1]
            if not isinstance(parent_obj, list):
                return
            if isinstance(last_op, slice):
                del parent_obj[last_op]
            else:
                idx = last_op
                if idx < 0:
                    idx += len(parent_obj)
                if 0 <= idx < len(parent_obj):
                    del parent_obj[idx]
        else:
            # No array ops => we want to delete the final_key from parent-of-final_key
            # But we stepped in if final_key was present => so we are "inside" that item.
            # => we can't do "del"
            # => If you want to support e.g. "del c['abc']", you need a different approach
            pass  # or raise an error or do something else

    # -------------------------------------------------------------------------
    #  Internals
    # -------------------------------------------------------------------------

    @classmethod
    def _parse_path(cls, path_name: str) -> List[Token]:
        """
        Parse a path like "foo.bar[2].baz[-1][3:7]"
        => [("foo", []), ("bar", [2]), ("baz", [-1, slice(3,7)])].
        """
        bracket_pattern = re.compile(r"\[([^\]]*)\]")
        segments = path_name.split(".")
        tokens: List[Container.Token] = []

        for segment in segments:
            base_key = segment.split("[", 1)[0]  # up to the first '['
            bracket_contents = bracket_pattern.findall(segment)
            array_ops = []
            for bc in bracket_contents:
                if ":" in bc:
                    start_str, end_str = bc.split(":", 1)
                    start = int(start_str) if start_str else None
                    end = int(end_str) if end_str else None
                    array_ops.append(slice(start, end))
                else:
                    idx = int(bc)
                    array_ops.append(idx)
            tokens.append((base_key, array_ops))

        return tokens


# Helper function to store something into a parent container (dict or list)
def _store_in_parent(parent: Any, key_or_index: Union[str, int], value: Any) -> None:
    """
    If `parent` is a dict, do parent[key] = value.
    If `parent` is a list, do parent[index] = value.
    """
    if isinstance(parent, dict):
        parent[key_or_index] = value
    elif isinstance(parent, list):
        parent[key_or_index] = value
    else:
        raise TypeError(f"Parent must be dict or list, got {type(parent).__name__}")
