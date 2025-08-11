#!/usr/bin/env python3
"""
Command Line Interface for JSON to YAML Schema Converter
"""

import argparse
import logging
import sys

from .converter import JSONToYAMLConverter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="JSON to YAML Schema Converter")
    parser.add_argument(
        "--folder",
        default="sample_data",
        help="Folder containing JSON files (default: sample_data)",
    )

    args = parser.parse_args()

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
