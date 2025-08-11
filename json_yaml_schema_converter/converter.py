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


def read_json_file(file_path: Path) -> Dict[Any, Any]:
    """Read and parse JSON file"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            logger.info(f"✅ Successfully read JSON file: {file_path.name}")
            # extract only first record
            return data[0] if data else None
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing JSON in {file_path.name}: {e}")
        return {}
    except FileNotFoundError:
        logger.error(f"❌ File not found: {file_path}")
        return {}
    except Exception as e:
        logger.error(f"❌ Error reading {file_path.name}: {e}")
        return {}


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

    def process_single_file(self, json_file: str) -> bool:
        """Process a single JSON file"""
        json_path = self.sample_data_folder / json_file

        if not json_path.exists():
            logger.info(f"❌ JSON file not found: {json_path}")
            return False

        # Read JSON data
        json_data = read_json_file(json_path)
        if not json_data:
            return False

        # Create output YAML file path
        yaml_filename = json_path.stem + ".yaml"
        yaml_path = self.output_folder / yaml_filename

        # Convert and save
        return self.convert_to_yaml(json_data, yaml_path)

    def process_all_json_files(self) -> List[str]:
        """Process all JSON files in the sample_data folder"""
        json_files = list(self.sample_data_folder.glob("*.json"))

        if not json_files:
            logger.debug(f"❌ No JSON files found in {self.sample_data_folder}")
            return []

        logger.debug(f"🔍 Found {len(json_files)} JSON file(s) to process")

        processed_files = []

        for json_file in json_files:
            logger.info(f"\n📄 Processing: {json_file.name}")

            # Read JSON data
            json_data = read_json_file(json_file)
            if not json_data:
                continue

            # Create output YAML file path
            yaml_filename = json_file.stem + ".yaml"
            yaml_path = self.output_folder / yaml_filename

            # Convert and save
            if self.convert_to_yaml(json_data, yaml_path):
                processed_files.append(yaml_filename)

        return processed_files

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

                    # Updated
                    if isinstance(data, str):
                        if is_datetime_string(data):
                            property_def["format"] = "date-time"
                        elif is_epoch_millis_timestamp(data):
                            property_def["format"] = "epoch-millis"
                    elif isinstance(data, int) and is_epoch_millis_timestamp(data):
                        if is_datetime_string(data):
                            property_def["format"] = "date-time"
                        elif is_epoch_millis_timestamp(data):
                            property_def["format"] = "epoch-millis"
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
