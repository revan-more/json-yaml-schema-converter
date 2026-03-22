#!/usr/bin/env python3
"""
Command Line Interface for JSON to YAML Schema Converter
"""

import argparse
import logging
import sys
from pathlib import Path

from .converter import JSONToYAMLConverter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="JSON to YAML Schema Converter")
    parser.add_argument(
        "--folder",
        required=True,
        help="Path to the folder containing JSON files to convert (required)",
    )

    args = parser.parse_args()

    # Validate the folder exists
    folder_path = Path(args.folder)
    if not folder_path.exists():
        logger.error(f"❌ Folder not found: '{args.folder}'")
        logger.error("   Please provide a valid path to a folder containing JSON files.")
        return 1

    if not folder_path.is_dir():
        logger.error(f"❌ '{args.folder}' is not a directory.")
        return 1

    # Check that the folder contains JSON files
    json_files = list(folder_path.glob("*.json"))
    if not json_files:
        logger.error(f"❌ No JSON files found in '{args.folder}'")
        logger.error("   Make sure the folder contains .json files to convert.")
        return 1

    # Initialize converter
    converter = JSONToYAMLConverter(args.folder)

    logger.info("🤖 JSON to YAML Schema Converter")
    logger.info("=" * 40)
    logger.info(
        f"\n📁 Processing all JSON files in '{converter.sample_data_folder}' folder..."
    )
    processed_files = converter.process_all_json_files()

    if processed_files:
        logger.info(f"\n✅ Successfully converted {len(processed_files)} file(s):")
        for file in processed_files:
            logger.info(f"   - {file}")
        logger.info(f"\n📂 Output files saved in: {converter.output_folder},"
                    f" it will take some time to generate the types file")
        return 0
    else:
        logger.info("\n❌ No files were processed successfully")
        return 1


if __name__ == "__main__":
    sys.exit(main())
