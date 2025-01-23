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
            path (str, optional): Ziel-Verzeichnis. Falls None wird das Nutzer-Home-Verzeichnis + 'offerme_data' genommen.
            file_name (str, optional): Dateiname. Falls None wird der Container-Name genutzt.
            indent (int, optional): JSON-Einrückung.

        Returns:
            bool
        """
        if path is None:
            path = os.path.join(os.path.expanduser("~"), "offerme_data")
        if file_name is None:
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

        current_obj = self._data
        parent_obj = None
        parent_key = None

        for i, (base_key, array_ops) in enumerate(tokens):
            is_last_token = i == len(tokens) - 1

            # 1) Dictionary-step
            if base_key:
                if not isinstance(current_obj, dict):
                    # Force overwrite
                    if parent_obj is not None:
                        new_dict = {}
                        _store_in_parent(parent_obj, parent_key, new_dict)
                        current_obj = new_dict
                    else:
                        self._data = {}
                        current_obj = self._data

                if base_key not in current_obj or not isinstance(
                    current_obj[base_key], (dict, list)
                ):
                    current_obj[base_key] = {}

                parent_obj = current_obj
                parent_key = base_key
                current_obj = current_obj[base_key]

            # 2) Array-ops
            for op in array_ops:
                if not isinstance(current_obj, list):
                    new_list = []
                    _store_in_parent(parent_obj, parent_key, new_list)
                    current_obj = new_list

                if isinstance(op, slice):
                    current_obj = current_obj[op]
                else:
                    idx = op
                    if idx < 0:
                        idx += len(current_obj)
                    if idx >= len(current_obj):
                        current_obj.extend([None] * (idx - len(current_obj) + 1))
                    if current_obj[idx] is None:
                        current_obj[idx] = {}
                    parent_obj = current_obj
                    parent_key = idx
                    current_obj = current_obj[idx]

            if is_last_token:
                # Do final assignment
                if array_ops:
                    _store_in_parent(parent_obj, parent_key, value)
                else:
                    _store_in_parent(parent_obj, parent_key, value)

    def get_value(self, path_name: str, default: Any = None) -> Any:
        """
        Retrieve the value at `path_name`. Returns `default` if the path is missing or invalid.

        Example:
          c.get_value("abc") -> c._data["abc"]
          c.get_value("abc.def[2].ghi") -> deeper fetch
        """
        if not path_name:
            raise ValueError("Missing path name.")
        tokens = self._parse_path(path_name)
        if not tokens:
            return default

        current_obj = self._data
        for base_key, array_ops in tokens:
            # Dictionary step
            if base_key:
                if not isinstance(current_obj, dict):
                    return default
                if base_key not in current_obj:
                    return default
                current_obj = current_obj[base_key]

            # Array-ops
            for op in array_ops:
                if not isinstance(current_obj, list):
                    return default
                if isinstance(op, slice):
                    try:
                        current_obj = current_obj[op]
                    except:
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

        parent_obj = self._data
        for base_key, array_ops in tokens[:-1]:
            if base_key:
                if not isinstance(parent_obj, dict):
                    return
                if base_key not in parent_obj:
                    return
                parent_obj = parent_obj[base_key]

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

        final_key, final_ops = tokens[-1]

        # Dictionary step if final_key
        if final_key:
            if not isinstance(parent_obj, dict):
                return
            if final_key not in parent_obj:
                return
            parent_obj = parent_obj[final_key]

        # Now handle final array ops
        if final_ops:
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

            # last op => del
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
            # Kein finaler array_op => wir haben nur del_entry für
            # den Fall "abc.def[2].ghi" etc.
            # Hier könnte man optional loggen oder eine Exception werfen,
            # falls man z.B. "del c['abc']" erwartet.
            pass

    # -------------------------------------------------------------------------
    #  Neue Methoden für Insert, Append, Remove
    # -------------------------------------------------------------------------

    def insert(self, path_name: str, index: int, value: Any) -> None:
        """
        Insert `value` at position `index` in a list located at `path_name`.
        Raises TypeError if the target is not a list.

        Example:
            c.set_value("mylist", [10, 20, 30])
            c.insert("mylist", 1, 15)  # -> [10, 15, 20, 30]
        """
        container = self.get_value(path_name)
        if not isinstance(container, list):
            raise TypeError(
                f"Object at path '{path_name}' is not a list; cannot insert."
            )
        container.insert(index, value)

    def append(self, path_name: str, value: Any) -> None:
        """
        Append `value` to a list located at `path_name`.
        Raises TypeError if the target is not a list.

        Example:
            c.set_value("mylist", [10, 20])
            c.append("mylist", 30)  # -> [10, 20, 30]
        """
        container = self.get_value(path_name)
        if not isinstance(container, list):
            raise TypeError(
                f"Object at path '{path_name}' is not a list; cannot append."
            )
        container.append(value)

    def remove(self, path_name: str, key_or_value: Any) -> None:
        """
        Remove an element (in a list) or a key (in a dict) within the object at `path_name`.

        - If the target is a list, this method removes the *first occurrence* of `key_or_value`.
          (Equivalent to list.remove(value).)

        - If the target is a dict, it interprets `key_or_value` as the dictionary key to delete.
          (Equivalent zu del dict[key].)

        Raises:
            TypeError: Wenn der Zielpfad weder Liste noch Dictionary enthält.
            ValueError oder KeyError: Falls der zu entfernende Wert/Key nicht existiert.
        """
        container = self.get_value(path_name)
        if isinstance(container, list):
            # Entfernt das erste Vorkommen von key_or_value
            container.remove(key_or_value)
        elif isinstance(container, dict):
            # Entfernt den Eintrag zum Key `key_or_value`
            if key_or_value in container:
                del container[key_or_value]
            else:
                raise KeyError(
                    f"Key '{key_or_value}' not found in dict at path '{path_name}'."
                )
        else:
            raise TypeError(
                f"Object at path '{path_name}' is neither a list nor a dict; cannot remove element."
            )

    def pop(self, path_name: str, index: int) -> Union[Dict[str, Any], Any]:
        """
        Entfernt und gibt das Element an Position `index` in der Liste am Pfad `path_name` zurück.
        Beispiel:
            c.set_value("mylist", [10, 20, 30])
            val = c.pop("mylist", 1)  # val = 20 -> Liste ist jetzt [10, 30]
        """
        container = self.get_value(path_name)
        if not isinstance(container, list):
            raise TypeError(
                f"Object at path '{path_name}' is not a list; cannot pop(index)."
            )
        return container.pop(index)

    def pop(self, path_name: str) -> Union[Dict[str, Any], Any]:
        """
        Entfernt und gibt ein Element basierend auf Slice oder Dict-Key am Pfad `path_name` zurück.

        - Ist der letzte Teil des Pfades (z.B. '...[start:end]') ein Slice, wird genau dieser Slice
        aus der entsprechenden Liste entfernt und als neue (Teil-)Liste zurückgegeben.

        - Ist der letzte Teil kein Slice und wir befinden uns in einem Dictionary, wird der
        entsprechende Key entfernt (dict.pop(key)) und dessen Wert zurückgegeben.

        - Ist der letzte Teil ein einfacher Listen-Index (z.B. '...[2]'), wird das Element
        an Index 2 entfernt und zurückgegeben.

        Beispiele:
            1. Slice-Pop
                c.set_value("mylist", [10, 20, 30, 40, 50])
                sub = c.pop("mylist[1:4]")  # sub = [20, 30, 40], mylist -> [10, 50]

            2. Dict-Pop
                c.set_value("settings", {"theme": "dark", "volume": 10})
                old_value = c.pop("settings.theme")  # old_value = "dark", settings -> {"volume": 10}

            3. Einzelner Listen-Index (ohne zweiten Parameter):
                c.set_value("numbers", [100, 200, 300])
                val = c.pop("numbers[1]")  # val = 200, numbers -> [100, 300]
        """
        if not path_name:
            raise ValueError("Missing path name.")

        tokens = self._parse_path(path_name)
        if not tokens:
            raise ValueError("Path has no tokens (empty).")

        # Wie in del_entry: wir navigieren zum "Eltern-Objekt" des letzten Tokens
        # und entfernen dann gezielt den letzten Token (Slice, Index oder Dict-Key).
        parent_obj = self._data

        # Gehe alle Tokens außer den letzten durch, um den Container zu finden,
        # in dem wir das letzte Element tatsächlich entfernen:
        for base_key, array_ops in tokens[:-1]:
            if base_key:
                if not isinstance(parent_obj, dict):
                    # Pfad ungültig
                    raise KeyError(
                        f"Cannot pop: dict expected, got {type(parent_obj).__name__} instead."
                    )
                if base_key not in parent_obj:
                    raise KeyError(f"Key '{base_key}' not found in parent dict.")
                parent_obj = parent_obj[base_key]

            for op in array_ops:
                if not isinstance(parent_obj, list):
                    raise TypeError(
                        f"Cannot pop: list expected, got {type(parent_obj).__name__} instead."
                    )
                if isinstance(op, slice):
                    try:
                        parent_obj = parent_obj[op]
                    except:
                        raise IndexError(f"Invalid slice operation '{op}' on list.")
                else:
                    idx = op
                    if idx < 0:
                        idx += len(parent_obj)
                    if idx < 0 or idx >= len(parent_obj):
                        raise IndexError(f"Index '{op}' out of range.")
                    if parent_obj[idx] is None:
                        raise ValueError("Cannot pop from None element.")
                    parent_obj = parent_obj[idx]

        # Letzter Token:
        final_key, final_ops = tokens[-1]

        # 1) Falls es ein 'base_key' (final_key) gibt, navigieren wir erstmal rein:
        #    Dann wird final_ops interpretiert als evtl. Listenoperation.
        if final_key:
            if not isinstance(parent_obj, dict):
                raise TypeError(
                    f"Cannot pop dict-key '{final_key}': parent is not a dict."
                )
            if final_key not in parent_obj:
                raise KeyError(f"Key '{final_key}' not found in parent dict.")
            parent_obj = parent_obj[final_key]

        # 2) Nun bearbeiten wir final_ops (kann Slice, Index oder nichts sein).
        if final_ops:
            # Navigiere alle bis auf den letzten
            for op in final_ops[:-1]:
                if not isinstance(parent_obj, list):
                    raise TypeError(
                        f"Cannot pop from list: got {type(parent_obj).__name__}."
                    )
                if isinstance(op, slice):
                    try:
                        parent_obj = parent_obj[op]
                    except:
                        raise IndexError(f"Invalid slice '{op}' on list.")
                else:
                    idx = op
                    if idx < 0:
                        idx += len(parent_obj)
                    if idx < 0 or idx >= len(parent_obj):
                        raise IndexError(f"Index '{op}' out of range.")
                    if parent_obj[idx] is None:
                        raise ValueError("Cannot pop from None element.")
                    parent_obj = parent_obj[idx]

            # Letzter op => pop-Operation (Index oder Slice)
            last_op = final_ops[-1]

            if not isinstance(parent_obj, list):
                raise TypeError(
                    f"Cannot pop from list: got {type(parent_obj).__name__}."
                )

            if isinstance(last_op, slice):
                # Beispiel: "mylist[1:4]"
                # Wir holen uns das Teilstück, löschen es und geben es zurück.
                to_return = parent_obj[last_op]
                del parent_obj[last_op]
                return to_return
            else:
                # single index
                idx = last_op
                if idx < 0:
                    idx += len(parent_obj)
                if idx < 0 or idx >= len(parent_obj):
                    raise IndexError(f"Index '{idx}' out of range.")
                return parent_obj.pop(idx)

        else:
            # Keine final_ops => Es liegt also ein Dictionary-Eintrag vor, den wir poppen.
            # ABER wir müssen nochmal eins zurück gehen, weil wir gerade "im" final_key sind.
            # Sprich: Im aktuellen Code sind wir *im* dict, dessen Eintrag entfernt werden soll.
            #
            # Beispiel: "settings.theme" -> parent_obj ist jetzt `settings["theme"]` (also der Wert),
            # aber wir möchten ja `settings.pop("theme")` machen.
            #
            # Deswegen müssen wir den Pfad nochmal leicht anpassen:
            # (Siehe del_entry-Logik: Man löscht immer vom "Eltern-Container".)
            #
            # Wir gehen also einen Schritt zurück: Dann haben wir den "Eltern-Container" (= dict).
            # Dort machen wir pop(final_key).
            #
            # Final: Wir müssen den Wert zurückgeben.

            # Wir müssen zuerst den parent-Container finden:
            #  -> das war parent_obj, *bevor* wir "parent_obj = parent_obj[final_key]" gemacht haben.
            # Also müssen wir leider denselben Pfad nochmal laufen, aber *nur* bis tokens[-1],
            # und dann dort pop machen.
            # Oder wir ändern oben die Logik, damit wir hier nicht "zu weit" reinspringen.
            #
            # Der einfachste Weg: wir nutzen den Code von `del_entry` als Vorlage und machen
            #   pop() statt del ...
            #
            # -> Hier als vereinfachte Variante: wir rufen nochmal `self.get_value(...)`
            #    aber NUR für den Parent-Pfad. Dann poppen wir dort.
            #
            # (Oder wir schreiben die Logik um. Hier machen wir's kurz pragmatisch.)

            # Pfad ohne den letzten Key => der "Parent"-Pfad:
            # Falls unser originaler Pfad "abc.def.key" war, dann parent_path = "abc.def"
            # Falls unser originaler Pfad "abc.def[0].key" war,
            #    -> Dann tokens[-1] = (key, [])
            #    -> parent_path -> "abc.def[0]"
            #
            # Wir bauen also die tokens ohne den letzten Token zusammen und rufen .get_value() auf.

            if len(tokens) == 1:
                # Dann gibt es keinen echten "Parent"-Pfad, wir poppen direkt aus self._data
                parent_container = self._data
                final_key_only = tokens[0][0]  # base_key
            else:
                parent_tokens = tokens[:-1]
                # Wir bauen den Pfad aus den parent_tokens wieder zusammen:
                parent_path_str = self._rebuild_path(parent_tokens)
                parent_container = self.get_value(parent_path_str)
                final_key_only = tokens[-1][
                    0
                ]  # base_key (der eigentliche Key im letzten Token)

            if not isinstance(parent_container, dict):
                raise TypeError("Parent object is not a dict, cannot pop dict-key.")

            return parent_container.pop(final_key_only)

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
            base_key = segment.split("[", 1)[0]
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

    # -----------------------------------------------------------------------------
    # Hilfsfunktion um den Pfad aus Tokens wieder zusammenzubauen
    # -----------------------------------------------------------------------------
    @classmethod
    def _rebuild_path(cls, tokens: List[Token]) -> str:
        """
        Baut aus einer Liste von Tokens wieder einen Path-String zusammen
        (z.B. [("abc",[]),("def",[0]),("xyz",[])] -> "abc.def[0].xyz").

        Wird benötigt, um den "Eltern-Pfad" zu rekonstruieren.
        """
        path_parts = []
        for base_key, array_ops in tokens:
            part = base_key
            for op in array_ops:
                if isinstance(op, slice):
                    start = "" if op.start is None else str(op.start)
                    end = "" if op.stop is None else str(op.stop)
                    part += f"[{start}:{end}]"
                else:
                    part += f"[{op}]"
            path_parts.append(part)
        return ".".join(path_parts)


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
