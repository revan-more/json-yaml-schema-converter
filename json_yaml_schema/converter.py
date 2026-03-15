#!/usr/bin/env python3
"""
JSON to YAML Converter
Reads JSON API response files from sample_data
folder and converts them to YAML format
"""
import logging
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_title_from_key(key: str) -> str:
    """Generate human-readable title from JSON key"""
    # Handle snake_case and camelCase
    if "_" in key:
        # snake_case
        words = key.split("_")
    else:
        # camelCase or PascalCase
        import re

        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", key)

    # Capitalize first letter of each word
    title = " ".join(word.capitalize() for word in words)

    # Handle common abbreviations
    abbreviations = {
        "Id": "ID",
        "Url": "URL",
        "Api": "API",
        "Http": "HTTP",
        "Json": "JSON",
        "Xml": "XML",
        "Uuid": "UUID",
        "Utc": "UTC",
        "Gmt": "GMT",
    }

    for abbr, replacement in abbreviations.items():
        title = title.replace(abbr, replacement)

    return title


def is_epoch_millis_timestamp(data):
    """Check if data is an epoch milliseconds timestamp (string or int)"""
    try:
        if isinstance(data, str):
            # Check if string contains only digits
            if not data.isdigit():
                return False
            timestamp = int(data)
        elif isinstance(data, int):
            timestamp = data
        else:
            return False

        # Epoch millis should be 13 digits (roughly between 1970-2050)
        # Valid range: 1000000000000 (2001) to 2147483647000 (2038)
        if (
            len(str(timestamp)) == 13
            and 1000000000000 <= timestamp <= 2147483647000
        ):
            # Try to convert to datetime to validate
            datetime.fromtimestamp(timestamp / 1000)
            return True
        return False
    except (ValueError, OSError, OverflowError):
        return False


def is_datetime_string(value: str) -> bool:
    """Check if a string appears to be a date-time value"""
    if not isinstance(value, str):
        return False

    # Common date-time patterns
    datetime_patterns = [
        # ISO 8601 formats
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?"
    ]
    return any(re.match(pattern, value) for pattern in datetime_patterns)


def is_ip_address(value: str) -> bool:
    """Check if a string is an IP address (IPv4 or IPv6)"""
    if not isinstance(value, str) or not value:
        return False

    # IPv4 pattern - more precise
    ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"

    # Check IPv4 first
    if re.match(ipv4_pattern, value):
        return True
    return False


def is_mac_address(value: str) -> bool:
    """Check if a string is a MAC address"""
    if not isinstance(value, str):
        return False

    # MAC address patterns (with : or -)
    mac_patterns = [
        r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",  # AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF
        r"^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$"  # AAAA.BBBB.CCCC
    ]

    return any(re.match(pattern, value) for pattern in mac_patterns)


def get_type_from_value(value: Any) -> str:
    """Map Python types to schema types"""
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, str):
        return "string"
    # elif value is None:
    #     return "string"
    else:
        return "string"


def read_all_records(file_path: Path) -> List[Dict[Any, Any]]:
    """Read and parse JSON file, returning ALL records (not just the first).
    Handles both array responses [...] and single object responses {...}.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            logger.info(f"✅ Successfully read JSON file: {file_path.name}")

            if isinstance(data, list):
                # Array of records — return all of them
                logger.info(f"   📊 Found {len(data)} record(s) in {file_path.name}")
                return [r for r in data if isinstance(r, dict)]
            elif isinstance(data, dict):
                # Single object response
                return [data]
            else:
                logger.warning(f"⚠️ Unexpected root type in {file_path.name}: {type(data)}")
                return []
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing JSON in {file_path.name}: {e}")
        return []
    except FileNotFoundError:
        logger.error(f"❌ File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"❌ Error reading {file_path.name}: {e}")
        return []


def read_json_file(file_path: Path) -> Dict[Any, Any]:
    """Read and parse JSON file (legacy — returns first record only)"""
    records = read_all_records(file_path)
    return records[0] if records else {}


def deep_merge_schemas(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively deep-merge two schema dicts so every property from both is kept.

    Rules:
    - If a key exists only in one dict, it is kept as-is.
    - If both dicts have the same key and both values are dicts, merge recursively.
    - For 'properties' sub-dicts inside objects, merge recursively.
    - For array items that are objects, merge their properties recursively.
    - Type upgrade: if one side is a simple type (e.g. string from null) and the other
      is a richer type (object/array with properties), the richer schema wins.
    """
    merged = dict(base)  # shallow copy of base

    for key, inc_value in incoming.items():
        if key not in merged:
            # New property — add it
            merged[key] = inc_value
        else:
            base_value = merged[key]
            # Both are dicts — need recursive merge
            if isinstance(base_value, dict) and isinstance(inc_value, dict):
                base_has_props = "properties" in base_value
                inc_has_props = "properties" in inc_value
                base_has_items = "items" in base_value
                inc_has_items = "items" in inc_value

                # Type upgrade: base is simple (no properties/items), incoming is richer
                if not base_has_props and not base_has_items and (inc_has_props or inc_has_items):
                    merged[key] = inc_value
                # Type upgrade: incoming is simple, base is richer — keep base
                elif (base_has_props or base_has_items) and not inc_has_props and not inc_has_items:
                    pass  # keep base_value
                # Both have 'properties', merge the properties recursively
                elif base_has_props and inc_has_props:
                    merged_props = deep_merge_schemas(
                        base_value["properties"], inc_value["properties"]
                    )
                    merged[key] = {**base_value, **inc_value, "properties": merged_props}
                # Both are array types with object items, merge item properties
                elif (
                    base_value.get("type") == "array"
                    and inc_value.get("type") == "array"
                    and isinstance(base_value.get("items"), dict)
                    and isinstance(inc_value.get("items"), dict)
                    and "properties" in base_value.get("items", {})
                    and "properties" in inc_value.get("items", {})
                ):
                    merged_item_props = deep_merge_schemas(
                        base_value["items"]["properties"],
                        inc_value["items"]["properties"],
                    )
                    merged[key] = {
                        **base_value,
                        "items": {**base_value["items"], "properties": merged_item_props},
                    }
                else:
                    # Generic dict merge (e.g. both are simple property defs)
                    merged[key] = deep_merge_schemas(base_value, inc_value)
            # else: keep base_value (type already captured)

    return merged


class JSONToYAMLConverter:
    """AI Agent for converting JSON API responses to YAML format"""

    def __init__(self, sample_data_folder: str = "build/output"):
        self.sample_data_folder = Path(sample_data_folder)
        self.output_folder = self.sample_data_folder / "yaml_output"
        if not self.output_folder.exists():
            self.ensure_directories()

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.sample_data_folder.mkdir(exist_ok=True)
        self.output_folder.mkdir(exist_ok=True)

    def convert_to_yaml(self, data: Dict[Any, Any], output_path: Path) -> bool:
        """Convert JSON data to YAML schema format and save"""
        try:
            # Generate schema from JSON data
            schema = self.generate_schema_from_json(data)

            # Configure YAML output format
            yaml_content = yaml.dump(
                schema,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
                sort_keys=False,
            )

            with open(output_path, "w", encoding="utf-8") as file:
                file.write(yaml_content)

            logger.info(f"✅ Successfully converted to YAML schema: {output_path.name}")
            return True

        except Exception as e:
            logger.info(f"❌ Error converting to YAML: {e}")
            return False

    def _merge_all_records_schema(self, records: List[Dict[Any, Any]]) -> Dict[str, Any]:
        """Generate a merged schema from ALL records in a file.
        Iterates through every record and deep-merges the schemas so that
        no property is missed — even if it only appears in one record.
        """
        merged_schema = {}

        for i, record in enumerate(records):
            record_schema = self.generate_schema_from_json(record)
            if not merged_schema:
                merged_schema = record_schema
            else:
                merged_schema = deep_merge_schemas(merged_schema, record_schema)

        logger.info(f"   🔀 Merged schema across {len(records)} record(s)")
        return merged_schema

    def process_single_file(self, json_file: str) -> bool:
        """Process a single JSON file — reads ALL records and merges schemas"""
        json_path = self.sample_data_folder / json_file

        if not json_path.exists():
            logger.info(f"❌ JSON file not found: {json_path}")
            return False

        # Read ALL records from the file
        records = read_all_records(json_path)
        if not records:
            return False

        # Merge schemas from all records
        merged_schema = self._merge_all_records_schema(records)

        # Create output YAML file path
        yaml_filename = json_path.stem + ".yaml"
        yaml_path = self.output_folder / yaml_filename

        # Save the merged schema
        return self._save_schema_to_yaml(merged_schema, yaml_path)

    def _group_files_by_endpoint(self, json_files: List[Path]) -> Dict[str, List[Path]]:
        """Group JSON files by endpoint name.
        Files like NautobotDevice.json, NautobotDevice.0001.json, NautobotDevice.0002.json
        all belong to the same 'NautobotDevice' endpoint.
        """
        groups: Dict[str, List[Path]] = {}
        for f in sorted(json_files):
            # Strip paginated suffix: NautobotDevice.0001.json → NautobotDevice
            # Also handles: NautobotDevice.json → NautobotDevice
            endpoint = re.sub(r'\.\d+$', '', f.stem)
            groups.setdefault(endpoint, []).append(f)
        return groups

    def process_all_json_files(self) -> List[str]:
        """Process all JSON files in the sample_data folder.
        Groups paginated files by endpoint name (e.g. Endpoint.json + Endpoint.0001.json
        are treated as a single endpoint). Reads ALL records from ALL pages and deep-merges
        their schemas into one complete YAML per endpoint — no properties are missed.
        """
        json_files = list(self.sample_data_folder.glob("*.json"))

        if not json_files:
            logger.debug(f"❌ No JSON files found in {self.sample_data_folder}")
            return []

        # Group files by endpoint
        endpoint_groups = self._group_files_by_endpoint(json_files)
        logger.info(f"🔍 Found {len(json_files)} JSON file(s) across {len(endpoint_groups)} endpoint(s)")

        processed_files = []

        for endpoint, files in endpoint_groups.items():
            logger.info(f"\n🔗 Endpoint: {endpoint} ({len(files)} file(s))")

            # Collect ALL records across ALL paginated files for this endpoint
            all_records = []
            for json_file in files:
                logger.info(f"   📄 Reading: {json_file.name}")
                records = read_all_records(json_file)
                if records:
                    all_records.extend(records)

            if not all_records:
                logger.warning(f"   ⚠️ No valid records found for endpoint {endpoint}, skipping")
                continue

            logger.info(f"   📊 Total records across all pages: {len(all_records)}")

            # Merge schemas from ALL records across ALL pages
            merged_schema = self._merge_all_records_schema(all_records)

            # One YAML per endpoint
            yaml_filename = endpoint + ".yaml"
            yaml_path = self.output_folder / yaml_filename

            # Save the merged schema
            if self._save_schema_to_yaml(merged_schema, yaml_path):
                processed_files.append(yaml_filename)

        return processed_files

    def _save_schema_to_yaml(self, schema: Dict[str, Any], output_path: Path) -> bool:
        """Save a schema dict to a YAML file"""
        try:
            yaml_content = yaml.dump(
                schema,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
                sort_keys=False,
            )

            with open(output_path, "w", encoding="utf-8") as file:
                file.write(yaml_content)

            logger.info(f"✅ Successfully saved YAML schema: {output_path.name}")
            return True

        except Exception as e:
            logger.info(f"❌ Error saving YAML: {e}")
            return False

    def generate_schema_from_json(
        self, data: Any, parent_key: str = ""
    ) -> Dict[str, Any]:
        """Generate schema properties from JSON data"""
        if isinstance(data, dict):
            properties = {}

            for key, value in data.items():
                # Generate title from key
                title = generate_title_from_key(key)

                if isinstance(value, dict):
                    # Nested object
                    properties[key] = {
                        "type": "object",
                        "title": title,
                        "properties": self.generate_schema_from_json(value, key),
                    }
                elif isinstance(value, list):
                    # Array
                    if value:
                        # Determine array item type from first element
                        first_item = value[0]
                        if isinstance(first_item, dict):
                            properties[key] = {
                                "type": "array",
                                "title": title,
                                "items": {
                                    "type": "object",
                                    "properties": self.generate_schema_from_json(
                                        first_item, key
                                    ),
                                },
                            }
                        else:
                            properties[key] = {
                                "type": "array",
                                "title": title,
                                "items": {"type": get_type_from_value(first_item)},
                            }
                    else:
                        properties[key] = {
                            "type": "array",
                            "title": title,
                            "items": {"type": "string"},
                        }
                else:
                    # Primitive type
                    property_def = {}

                    if get_type_from_value(value) == "boolean":
                        property_def["type"] = "boolean"
                        property_def["title"] = f"{title}?"
                    else:
                        property_def["type"] = get_type_from_value(value)
                        property_def["title"] = title

                    # Check for format (date-time, epoch-millis, ip-addr, mac-addr)
                    if isinstance(value, str) and is_datetime_string(value):
                        property_def["format"] = "date-time"
                    elif isinstance(value, (str, int)) and is_epoch_millis_timestamp(value):
                        property_def["format"] = "epoch-millis"
                    elif isinstance(value, str) and is_ip_address(value):
                        property_def["format"] = "ip-addr"
                    elif isinstance(value, str) and is_mac_address(value):
                        property_def["format"] = "mac-addr"
                    properties[key] = property_def

            return {"properties": properties} if parent_key == "" else properties
        else:
            # If root is not an object, wrap it
            root_property = {"type": get_type_from_value(data), "title": "Value"}

            # Updated version of your original code
            if isinstance(data, str):
                if is_datetime_string(data):
                    root_property["format"] = "date-time"
                elif is_epoch_millis_timestamp(data):
                    root_property["format"] = "epoch-millis"
            elif isinstance(data, int) and is_epoch_millis_timestamp(data):
                root_property["format"] = "epoch-millis"

        return {"properties": {"value": root_property}}


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="JSON to YAML Converter")
    # parser.add_argument(
    #     "--folder",
    #     required=True,
    #     help="Path to the folder containing your JSON files (required)",
    # )
    parser.add_argument(
        "--folder",
        default="build/output",
        help="Folder containing JSON files (default: build/output)",
    )

    args = parser.parse_args()

    # Initialize converter
    converter = JSONToYAMLConverter(args.folder)

    logger.info("JSON to YAML Converter")
    logger.info("=" * 40)
    logger.info(
        "\n📁 Processing all JSON files in '%s' folder...", converter.sample_data_folder
    )
    processed_files = converter.process_all_json_files()

    if processed_files:
        logger.info("\n✅ Successfully converted '%s' file(s):", {len(processed_files)})
        for file in processed_files:
            logger.info("   -'%s'", file)
        logger.info(f"\n📂 Output files saved in: {converter.output_folder},"
                    f" it may take some time to generate the types file")
    else:
        logger.error("\n❌ No files were processed successfully")


if __name__ == "__main__":
    main()
