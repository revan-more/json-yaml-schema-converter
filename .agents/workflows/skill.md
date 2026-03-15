---
description: How to process JSON API outputs to YAML schemas
---

# Objective
Convert JSON API response outputs into structured YAML schema files using the customized MCP tool.

# Trigger
When the user says something like:
- "create a json yaml file"
- "convert JSON files to YAML schema"
- "run the JSON to YAML converter"

# Instructions
1. Acknowledge the user's request.
2. **Ask the user** for the folder path where their JSON files are located.
   - Example: *"Which folder contains your JSON files? Please provide the full path."*
   - If the user already mentioned a path in their message (e.g., "from build/output"), use that path directly.
3. Ensure you have access to the `json_to_yaml` tool provided by the `JSON-YAML-Schema-Converter` MCP server.
   *(This tool should be configured and available in your environment via `json2yaml-mcp-server`)*
4. Call the `json_to_yaml` tool with the `folder_path` argument set to the path the user provided.
5. Wait for the tool to execute and read the JSON records.
6. Provide a summary of the conversion to the user, based on the tool's return string (e.g., stating how many files were processed and where the output is stored).
7. Inform the user they can review the generated YAML schema files in the `yaml_output` subdirectory inside their provided folder.
