import unittest

from gworld.schema import (
    KIND_ID_RE, SchemaError, ValidationError, check_schema, is_kind_id, validate,
)


def codes(artifact, schema):
    return [(e.path, e.code, e.params) for e in validate(artifact, schema)]


class KeywordTest(unittest.TestCase):
    def test_type_pass_fail(self):
        self.assertEqual(codes("a", {"type": "string"}), [])
        self.assertEqual(codes(1, {"type": "string"}), [("", "type", {"expected": "string"})])

    def test_type_list(self):
        self.assertEqual(codes(None, {"type": ["string", "null"]}), [])
        self.assertEqual(codes(1, {"type": ["string", "null"]}),
                         [("", "type", {"expected": ["string", "null"]})])

    def test_bool_not_integer_nor_number(self):
        self.assertEqual(codes(True, {"type": "integer"}), [("", "type", {"expected": "integer"})])
        self.assertEqual(codes(True, {"type": "number"}), [("", "type", {"expected": "number"})])
        self.assertEqual(codes(1.0, {"type": "integer"}), [("", "type", {"expected": "integer"})])
        self.assertEqual(codes(1.5, {"type": "number"}), [])
        self.assertEqual(codes(True, {"type": "boolean"}), [])

    def test_required(self):
        s = {"required": ["license"]}
        self.assertEqual(codes({"license": "MIT"}, s), [])
        self.assertEqual(codes({}, s), [("", "required", {"property": "license"})])

    def test_properties_nested_path(self):
        s = {"properties": {"cells": {"type": "array", "items": {
            "type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}}}}
        self.assertEqual(codes({"cells": [{"id": "a"}, {"id": "b"}, {"id": 3}]}, s),
                         [("/cells/2/id", "type", {"expected": "string"})])
        self.assertEqual(codes({"cells": [{}]}, s), [("/cells/0", "required", {"property": "id"})])

    def test_path_escaping(self):
        s = {"properties": {"a/b~c": {"type": "string"}}}
        self.assertEqual(codes({"a/b~c": 1}, s), [("/a~1b~0c", "type", {"expected": "string"})])

    def test_additional_properties_false(self):
        s = {"properties": {"a": {}}, "additionalProperties": False}
        self.assertEqual(codes({"a": 1}, s), [])
        self.assertEqual(codes({"a": 1, "z": 2}, s), [("", "additionalProperties", {"property": "z"})])

    def test_additional_properties_schema(self):
        s = {"additionalProperties": {"type": "integer"}}
        self.assertEqual(codes({"x": 1}, s), [])
        self.assertEqual(codes({"x": "s"}, s), [("/x", "type", {"expected": "integer"})])

    def test_property_names(self):
        s = {"propertyNames": {"pattern": "^[a-z]+$"}}
        self.assertEqual(codes({"abc": 1}, s), [])
        self.assertEqual(codes({"A": 1}, s),
                         [("", "propertyNames", {"property": "A", "code": "pattern"})])

    def test_min_properties(self):
        self.assertEqual(codes({"a": 1}, {"minProperties": 1}), [])
        self.assertEqual(codes({}, {"minProperties": 1}), [("", "minProperties", {"limit": 1})])

    def test_items_min_max_items(self):
        s = {"items": {"type": "integer"}, "minItems": 1, "maxItems": 2}
        self.assertEqual(codes([1, 2], s), [])
        self.assertEqual(codes([], s), [("", "minItems", {"limit": 1})])
        self.assertEqual(codes([1, 2, 3], s), [("", "maxItems", {"limit": 2})])
        self.assertEqual(codes([1, "x"], s), [("/1", "type", {"expected": "integer"})])

    def test_enum(self):
        s = {"enum": ["a", "b"]}
        self.assertEqual(codes("a", s), [])
        self.assertEqual(codes("c", s), [("", "enum", {"allowed": ["a", "b"]})])
        self.assertEqual(codes(True, {"enum": [1]}), [("", "enum", {"allowed": [1]})])

    def test_const(self):
        self.assertEqual(codes("gworld.pack/0", {"const": "gworld.pack/0"}), [])
        self.assertEqual(codes("x", {"const": "gworld.pack/0"}),
                         [("", "const", {"expected": "gworld.pack/0"})])

    def test_pattern(self):
        self.assertEqual(codes("abc", {"pattern": "b"}), [])
        self.assertEqual(codes("abc", {"pattern": "^b"}), [("", "pattern", {"pattern": "^b"})])

    def test_length(self):
        self.assertEqual(codes("ab", {"minLength": 2, "maxLength": 2}), [])
        self.assertEqual(codes("a", {"minLength": 2}), [("", "minLength", {"limit": 2})])
        self.assertEqual(codes("abc", {"maxLength": 2}), [("", "maxLength", {"limit": 2})])

    def test_minimum_maximum(self):
        s = {"minimum": 1, "maximum": 3}
        self.assertEqual(codes(2, s), [])
        self.assertEqual(codes(0, s), [("", "minimum", {"limit": 1})])
        self.assertEqual(codes(4, s), [("", "maximum", {"limit": 3})])

    def test_annotations_ignored(self):
        s = {"$schema": "x", "$id": "y", "$comment": "c", "title": "t", "description": "d",
             "default": 1, "examples": [1], "type": "integer"}
        self.assertEqual(codes(1, s), [])

    def test_validation_error_is_frozen(self):
        e = ValidationError("", "type", {})
        with self.assertRaises(Exception):
            e.path = "x"

    def test_bad_data_never_raises(self):
        s = {"type": "object", "required": ["a"], "properties": {"a": {"items": {}}}}
        for data in (None, 1, "s", [], {"a": 5}):
            validate(data, s)


class RefTest(unittest.TestCase):
    def test_ref_defs(self):
        s = {"$defs": {"id": {"type": "string", "minLength": 1}},
             "properties": {"a": {"$ref": "#/$defs/id"}}}
        self.assertEqual(codes({"a": "x"}, s), [])
        self.assertEqual(codes({"a": ""}, s), [("/a", "minLength", {"limit": 1})])

    def test_recursion_through_defs(self):
        s = {"$ref": "#/$defs/node", "$defs": {"node": {
            "type": "object", "required": ["name"],
            "properties": {"name": {"type": "string"},
                           "children": {"type": "array", "items": {"$ref": "#/$defs/node"}}}}}}
        ok = {"name": "r", "children": [{"name": "a", "children": [{"name": "b"}]}]}
        self.assertEqual(codes(ok, s), [])
        bad = {"name": "r", "children": [{"name": "a", "children": [{}]}]}
        self.assertEqual(codes(bad, s), [("/children/0/children/0", "required", {"property": "name"})])

    def test_root_ref(self):
        s = {"type": "object", "properties": {"next": {"$ref": "#"}}}
        self.assertEqual(codes({"next": {"next": 1}}, s),
                         [("/next/next", "type", {"expected": "object"})])

    def test_remote_ref_is_schema_error(self):
        for ref in ("http://x/y.json", "other.json#/a", "https://x#/a"):
            with self.assertRaisesRegex(SchemaError, "local"):
                check_schema({"$ref": ref})

    def test_ref_only_to_root_or_defs(self):
        for s in ({"enum": [{"foo": 1}], "$ref": "#/enum/0"},
                  {"properties": {"type": {"type": "string"}}, "$ref": "#/properties"}):
            with self.assertRaisesRegex(SchemaError, r"'#' o '#/\$defs/<nombre>'"):
                check_schema(s)

    def test_unresolved_ref(self):
        with self.assertRaisesRegex(SchemaError, "sin destino"):
            check_schema({"$ref": "#/$defs/nope"})

    def test_circular_ref(self):
        with self.assertRaisesRegex(SchemaError, "circular"):
            check_schema({"$ref": "#"})


class SchemaErrorTest(unittest.TestCase):
    def test_unknown_keyword(self):
        with self.assertRaisesRegex(SchemaError, "oneOf"):
            validate(1, {"oneOf": []})

    def test_format_rejected(self):
        with self.assertRaisesRegex(SchemaError, "format"):
            check_schema({"type": "string", "format": "uri"})

    def test_unknown_keyword_nested_in_defs(self):
        with self.assertRaisesRegex(SchemaError, "allOf"):
            check_schema({"$defs": {"a": {"allOf": []}}})

    def test_malformed_values(self):
        for bad in ({"type": "text"}, {"type": []}, {"required": "a"}, {"minLength": -1},
                    {"minLength": True}, {"pattern": "("}, {"enum": []}, {"minimum": "1"},
                    {"properties": []}, {"items": []}, {"additionalProperties": 1}):
            with self.assertRaises(SchemaError, msg=repr(bad)):
                check_schema(bad)

    def test_schema_not_object(self):
        with self.assertRaises(SchemaError):
            check_schema(True)


class OrderTest(unittest.TestCase):
    def test_deterministic_order(self):
        s = {"required": ["z", "a"],
             "properties": {"m": {"type": "string"}, "b": {"type": "string"}},
             "additionalProperties": False}
        data = {"m": 1, "b": 2, "y": 0, "x": 0}
        expected = [
            ("", "required", {"property": "a"}),
            ("", "required", {"property": "z"}),
            ("/b", "type", {"expected": "string"}),
            ("/m", "type", {"expected": "string"}),
            ("", "additionalProperties", {"property": "x"}),
            ("", "additionalProperties", {"property": "y"}),
        ]
        self.assertEqual(codes(data, s), expected)
        self.assertEqual(codes(dict(reversed(list(data.items()))), s), expected)


class KindIdTest(unittest.TestCase):
    def test_cases(self):
        self.assertTrue(is_kind_id("gworld.pack/0"))
        self.assertTrue(is_kind_id("gworld.canon/12"))
        for bad in ("gworld.pack/01", "Gworld.pack/0", "gworld/0", "gworld.pack", "gworld.pack/0\n", 3, None):
            self.assertFalse(is_kind_id(bad), repr(bad))

    def test_regex_text(self):
        self.assertEqual(KIND_ID_RE, r"^[a-z][a-z0-9]*\.[a-z][a-z0-9_.]*/(0|[1-9][0-9]*)$")


if __name__ == "__main__":
    unittest.main()
