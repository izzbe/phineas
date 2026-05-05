import yaml
from pathlib import Path

MAPPING_FILE = Path(__file__).parent / "mappings.yml"

with open(MAPPING_FILE, mode="r") as f:
    mappings = yaml.safe_load(f)

def get_mapping(schema: str):
    return mappings[schema]

def get_insert_cols(mapping: dict):
    return ", ".join(mapping.values())

def get_placeholders(mapping: dict):
    return ", ".join([f"${i}" for i in range(1, len(mapping.values()) + 1)])

def get_tuples(results: list[dict], mapping):
    return [tuple(r[col] for col in mapping.keys()) for r in results]

