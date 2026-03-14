#!/usr/bin/env python3
import json
import random
import sys
from datetime import datetime


def generate_example_for_property(property_schema, property_name=None):
    """Generate example data based on JSON schema property definition"""
    print("DEBUG: property_schema -> ", property_schema)
    if isinstance(property_schema, bool):
        return True if property_schema else {}

    if "example" in property_schema:
        return property_schema["example"]

    if "enum" in property_schema:
        return random.choice(property_schema["enum"])

    if "const" in property_schema:
        return property_schema["const"]

    property_type = property_schema.get("type", "string")

    if property_type == "object":
        result = {}
        if "properties" in property_schema:
            for prop_name, prop_schema in property_schema["properties"].items():
                result[prop_name] = generate_example_for_property(prop_schema, prop_name)
        return result

    elif property_type == "array":
        items = property_schema.get("items", {})
        min_items = property_schema.get("minItems", 1)
        max_items = property_schema.get("maxItems", min_items + 1)
        count = min(min_items, max_items)  # Ensure we generate at least minItems

        if "prefixItems" in property_schema:
            return [generate_example_for_property(item) for item in property_schema["prefixItems"]]
        else:
            return [generate_example_for_property(items) for _ in range(count)]

    elif property_type == "string":
        format_type = property_schema.get("format", "")
        pattern = property_schema.get("pattern", "")

        if format_type == "date-time":
            return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        elif format_type == "date":
            return datetime.now().strftime("%Y-%m-%d")
        elif format_type == "time":
            return datetime.now().strftime("%H:%M:%S")
        elif format_type == "email":
            return "example@example.com"
        elif format_type == "uri":
            return "https://example.com"
        elif pattern:
            # Very basic pattern handling
            if "\\d" in pattern:
                return "12345"
            else:
                return "example"
        else:
            if property_name and "nombre" in property_name.lower():
                return "Nombre de ejemplo"
            elif property_name and "codigo" in property_name.lower():
                return "COD12345"
            else:
                return "string"

    elif property_type == "number" or property_type == "integer":
        minimum = property_schema.get("minimum", 0)
        maximum = property_schema.get("maximum", minimum + 100)
        if property_type == "integer":
            return min(maximum, minimum + random.randint(0, 10))
        else:
            return min(maximum, minimum + random.uniform(0, 10))

    elif property_type == "boolean":
        return True

    elif property_type == "null":
        return None

    # Handle oneOf, anyOf, allOf
    if "oneOf" in property_schema:
        return generate_example_for_property(property_schema["oneOf"][0])

    if "anyOf" in property_schema:
        return generate_example_for_property(property_schema["anyOf"][0])

    if "allOf" in property_schema:
        combined = {}
        for schema in property_schema["allOf"]:
            print("DEBUG: generate_example_for_property(schema) ->", generate_example_for_property(schema))
            combined.update(generate_example_for_property(schema))
        return combined

    return "unknown"


def generate_example(schema):
    """Generate a complete example based on the JSON schema"""
    if "$ref" in schema:
        # Cannot handle external references in this simple script
        return {"error": "External references not supported"}

    if "type" in schema and schema["type"] == "object":
        return generate_example_for_property(schema)

    # Handle schemas with no type but with properties
    if "properties" in schema:
        example = {}
        for prop_name, prop_schema in schema["properties"].items():
            example[prop_name] = generate_example_for_property(prop_schema, prop_name)
        return example

    return {"error": "Could not generate example for schema"}


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python generate_json_example.py <schema_file.json> [output_file.json]")
        sys.exit(1)

    schema_file = sys.argv[1]

    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except Exception as e:
        print(f"Error loading schema file: {e}")
        sys.exit(1)

    example = generate_example(schema)

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(example, f, indent=2, ensure_ascii=False)
            print(f"Example JSON written to {output_file}")
        except Exception as e:
            print(f"Error writing output file: {e}")
            sys.exit(1)
    else:
        # Print to stdout
        print(json.dumps(example, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
