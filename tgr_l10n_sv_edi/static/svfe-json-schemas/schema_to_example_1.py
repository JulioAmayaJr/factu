import json
import sys

from faker import Faker
from jsonschema import Draft7Validator

fake = Faker()


def generate_example(schema):
    if "type" not in schema:
        return None

    schema_type = schema["type"]

    if isinstance(schema_type, list):
        schema_type = schema_type[0]

    if schema_type == "string":
        if "enum" in schema:
            return schema["enum"][0]
        if schema.get("format") == "date":
            return fake.date()
        if schema.get("format") == "email":
            return fake.email()
        if "pattern" in schema:
            return "pattern_value"
        if "minLength" in schema:
            return "x" * schema["minLength"]
        return fake.word()

    if schema_type == "integer":
        return schema.get("minimum", 1)

    if schema_type == "number":
        return float(schema.get("minimum", 1))

    if schema_type == "boolean":
        return True

    if schema_type == "array":
        item_schema = schema.get("items", {})
        min_items = schema.get("minItems", 1)
        return [generate_example(item_schema) for _ in range(min_items)]

    if schema_type == "object":
        obj = {}
        properties = schema.get("properties", {})
        required = schema.get("required", properties.keys())
        for prop in required:
            prop_schema = properties.get(prop, {})
            obj[prop] = generate_example(prop_schema)
        return obj

    return None


def main(schema_file, output_file="ejemplo_generado.json"):
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    example = generate_example(schema)

    # Validar el ejemplo contra el esquema
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(example), key=lambda e: e.path)
    if errors:
        print("Advertencia: el ejemplo generado puede no cumplir al 100% con el schema:")
        for error in errors:
            print(f"- {list(error.path)}: {error.message}")

    # Guardar en archivo
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(example, f, indent=4, ensure_ascii=False)

    print(f"Archivo '{output_file}' generado correctamente.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generar_ejemplo.py <archivo_schema.json>")
    else:
        schema_file = sys.argv[1]
        if sys.argv[2]:
            output_file = sys.argv[2]
            main(schema_file, output_file)
        main(schema_file)
