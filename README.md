# JSON to YAML Schema Converter

A powerful Python tool that converts JSON API responses into YAML schema format with proper type definitions, titles, and format specifications.

## Features

- ✅ **Smart Type Detection**: Automatically detects and maps JSON types to schema types
- ✅ **Date-Time Recognition**: Identifies datetime strings and adds `format: date-time`
- ✅ **Nested Object Support**: Handles complex nested JSON structures
- ✅ **Array Processing**: Properly processes arrays and their item types
- ✅ **Title Generation**: Creates human-readable titles from JSON keys
- ✅ **CLI Interface**: Easy-to-use command-line interface
- ✅ **Batch Processing**: Convert multiple JSON files at once

## Your api response file should look like this e.g
All json file should be `build/output` inside the folder or response would be like below
```json
[
    {
        "id": 12345,
        "name": "test Innovations Corp",
        "legal_name": "Tech Innovations Corporation Inc.",
        "founded_date": "2020-01-15",
        "incorporation_date": "2020-01-15T09:00:00Z",
        "tax_id": "12-3456789",
        "website": "https://testinnovations.com",
        "industry": "Software Technology",
        "employee_count": 250,
        "annual_revenue": 15000000.75,
        "is_public": true,
        "stock_symbol": null
    },
    {
        "id": 4565,
        "name": "demo Innovations Corp",
        "legal_name": "demo Innovations Corporation Inc.",
        "founded_date": "2020-01-15",
        "incorporation_date": "2020-01-15T09:00:00Z",
        "tax_id": "12-3456789",
        "website": "https://testinnovations.com",
        "industry": "Software Technology",
        "employee_count": 250,
        "annual_revenue": 15000000.75,
        "is_public": true,
        "stock_symbol": null
    },
]
```
# Command Line Interface (CLI)
```bash
# Use custom input folder
json2yaml_schema --folder my_api_data_folder
```

## Python API Usage
```python
from json_yaml_schema_converter import JSONToYAMLConverter

# Initialize converter
converter = JSONToYAMLConverter("path/to/json/files")

# Convert all JSON files
converted_files = converter.process_all_json_files()
```
