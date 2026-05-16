import yaml
from pathlib import Path
from models.models import *
from pydantic import TypeAdapter

MAPPING_FILE = Path(__file__).parent / "mappings.yml"

SCHEMAS = {
    "header": Header,
    "bars": Bar,
    "adjustment": Adjustment,
    "link": Link,
    "fundamentals_quarterly": FundamentalsQuarterly
}

with open(MAPPING_FILE, mode="r") as f:
    mappings = yaml.safe_load(f)

def get_mapping(schema_name: str):
    return mappings[schema_name]["schema"]

def get_insert_cols(mapping: dict):
    return ", ".join(mapping.values())

def get_placeholders(mapping: dict):
    return ", ".join([f"${i}" for i in range(1, len(mapping.values()) + 1)])

def get_url(schema_name: str):
    return mappings[schema_name]["url"]

def get_tuples(results: list[dict], schema: str, mapping):
    ta = TypeAdapter(list[SCHEMAS[schema]])
    validated = ta.validate_python(results)
    return [tuple(r.model_dump()[col] for col in mapping.keys()) for r in validated]
