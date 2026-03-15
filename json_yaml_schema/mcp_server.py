#!/usr/bin/env python3
"""
MCP Server for JSON to YAML Schema Converter
Exposes the JSON to YAML converter as an MCP tool.
"""

from pathlib import Path
from mcp.server.fastmcp import FastMCP
from json_yaml_schema.converter import JSONToYAMLConverter
import logging

# Initialize FastMCP Server
mcp = FastMCP("JSON-YAML-Schema-Converter")

logger = logging.getLogger(__name__)


@mcp.tool()
def json_to_yaml(folder_path: str) -> str:
    """
    Convert JSON API responses in a directory into YAML schema format.
    The tool automatically detects types, dates, and nested structures to generate proper YAML schema.
    Always ask the user to provide the folder path where their JSON files are located.

    Args:
        folder_path: Path to the folder containing the JSON files (must be provided by the user)
    """
    try:
        converter = JSONToYAMLConverter(sample_data_folder=folder_path)

        # Check if the folder exists
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            return f"Error: The input folder '{folder_path}' does not exist or is not a directory."

        processed_files = converter.process_all_json_files()

        if processed_files:
            return (
                f"Successfully converted {len(processed_files)} JSON file(s) to YAML schemas. "
                f"Output saved in '{converter.output_folder}'."
            )
        else:
            return f"No valid JSON files were found or processed in the folder '{folder_path}'."

    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        return f"An error occurred while running the conversion tool: {str(e)}"


def main():
    """Main function to run the MCP server over stdio"""
    mcp.run()


if __name__ == "__main__":
    main()
