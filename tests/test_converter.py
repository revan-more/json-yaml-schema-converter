#!/usr/bin/env python3
"""
Unit tests for JSON to YAML Schema Converter
"""

import unittest
import tempfile
import json
import shutil
import os
from pathlib import Path
import sys
import yaml

# Add the parent directory to the path to import the converter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from json_yaml_schema_converter.converter import JSONToYAMLConverter


class TestJSONToYAMLConverter(unittest.TestCase):
    """Test cases for JSONToYAMLConverter"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.converter = JSONToYAMLConverter(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_json_to_yaml_conversion(self):
        """Test basic JSON to YAML schema conversion"""
        test_data = {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "is_active": True,
            "created_at": "2024-01-15T10:30:00Z",
        }

        # Create test JSON file
        json_file = Path(self.temp_dir) / "test.json"
        with open(json_file, "w") as f:
            json.dump(test_data, f)

        # Convert to YAML
        success = self.converter.process_single_file("test.json")
        self.assertTrue(success)

        # Check output file exists
        yaml_file = Path(self.temp_dir) / "yaml_output" / "test.yaml"
        self.assertTrue(yaml_file.exists())

        # Load and validate YAML content
        with open(yaml_file, "r") as f:
            content = f.read()
            # Skip header and parse YAML
            yaml_content = content.split("---\n")[1]
            schema = yaml.safe_load(yaml_content)

        # Validate schema structure
        self.assertIn("properties", schema)
        properties = schema["properties"]

        # Check each field
        self.assertEqual(properties["id"]["type"], "integer")
        self.assertEqual(properties["id"]["title"], "ID")

        self.assertEqual(properties["name"]["type"], "string")
        self.assertEqual(properties["name"]["title"], "Name")

        self.assertEqual(properties["email"]["type"], "string")
        self.assertEqual(properties["email"]["title"], "Email")

        self.assertEqual(properties["is_active"]["type"], "boolean")
        self.assertEqual(properties["is_active"]["title"], "Is Active")

        self.assertEqual(properties["created_at"]["type"], "string")
        self.assertEqual(properties["created_at"]["title"], "Created At")
        self.assertEqual(properties["created_at"]["format"], "date-time")

    def test_nested_objects(self):
        """Test handling of nested objects"""
        test_data = {"user": {"profile": {"personal": {"age": 30, "city": "New York"}}}}

        schema = self.converter.generate_schema_from_json(test_data)

        self.assertIn("properties", schema)
        user_props = schema["properties"]["user"]["properties"]
        profile_props = user_props["profile"]["properties"]
        personal_props = profile_props["personal"]["properties"]

        self.assertEqual(personal_props["age"]["type"], "integer")
        self.assertEqual(personal_props["city"]["type"], "string")

    def test_array_handling(self):
        """Test handling of arrays"""
        test_data = {
            "users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}],
            "tags": ["admin", "user"],
            "scores": [85, 92, 78],
        }

        schema = self.converter.generate_schema_from_json(test_data)
        properties = schema["properties"]

        # Test object array
        self.assertEqual(properties["users"]["type"], "array")
        self.assertEqual(properties["users"]["items"]["type"], "object")
        user_props = properties["users"]["items"]["properties"]
        self.assertEqual(user_props["id"]["type"], "integer")
        self.assertEqual(user_props["name"]["type"], "string")

        # Test string array
        self.assertEqual(properties["tags"]["type"], "array")
        self.assertEqual(properties["tags"]["items"]["type"], "string")

        # Test number array
        self.assertEqual(properties["scores"]["type"], "array")
        self.assertEqual(properties["scores"]["items"]["type"], "integer")

    def test_datetime_detection(self):
        """Test date-time format detection"""
        test_cases = [
            ("2024-01-15T10:30:00Z", True),
            ("2024-01-15T10:30:00.123Z", True),
            ("2024-01-15T10:30:00+05:30", True),
            ("2024-01-15 10:30:00", True),
            ("2024-01-15", False),  # Date only, not datetime
            ("regular string", False),
            ("1642248600", True),  # Unix timestamp as string
            (1642248600, True),  # Unix timestamp as int
            (1642248600123, True),  # Unix timestamp in milliseconds
            (123, False),  # Too small to be timestamp
        ]

        for value, expected in test_cases:
            with self.subTest(value=value):
                result = self.converter.is_datetime_value(value)
                self.assertEqual(result, expected, f"Failed for value: {value}")

    def test_epoch_timestamp_detection(self):
        """Test epoch timestamp detection specifically"""
        test_data = {
            "created_timestamp": 1642248600,  # 10 digits - seconds
            "updated_timestamp": 1642248600123,  # 13 digits - milliseconds
            "micro_timestamp": 1642248600123456,  # 16 digits - microseconds
            "created_timestamp_str": "1642248600",  # String timestamp
            "regular_number": 123,  # Regular small number
            "large_id": 999999999999999999999,  # Very large number (not timestamp)
        }

        schema = self.converter.generate_schema_from_json(test_data)
        properties = schema["properties"]

        # Check integer timestamps
        self.assertEqual(properties["created_timestamp"]["type"], "integer")
        self.assertEqual(properties["created_timestamp"]["format"], "date-time")

        self.assertEqual(properties["updated_timestamp"]["type"], "integer")
        self.assertEqual(properties["updated_timestamp"]["format"], "date-time")

        self.assertEqual(properties["micro_timestamp"]["type"], "integer")
        self.assertEqual(properties["micro_timestamp"]["format"], "date-time")

        # Check string timestamp
        self.assertEqual(properties["created_timestamp_str"]["type"], "string")
        self.assertEqual(properties["created_timestamp_str"]["format"], "date-time")

        # Check regular number (should not have format)
        self.assertEqual(properties["regular_number"]["type"], "integer")
        self.assertNotIn("format", properties["regular_number"])

    def test_title_generation(self):
        """Test title generation from JSON keys"""
        test_cases = [
            ("user_id", "User ID"),
            ("firstName", "First Name"),
            ("api_key", "API Key"),
            ("created_at", "Created At"),
            ("isActive", "Is Active"),
            ("xmlHttpRequest", "Xml Http Request"),
            ("uuid", "UUID"),
            ("simple", "Simple"),
        ]

        for key, expected_title in test_cases:
            with self.subTest(key=key):
                title = self.converter.generate_title_from_key(key)
                self.assertEqual(title, expected_title)

    def test_merge_schemas(self):
        """Test schema merging for complete field coverage"""
        schema1 = {
            "properties": {
                "id": {"type": "integer", "title": "ID"},
                "name": {"type": "string", "title": "Name"},
            }
        }

        schema2 = {
            "properties": {
                "id": {"type": "integer", "title": "ID"},
                "email": {"type": "string", "title": "Email"},
            }
        }

        merged = self.converter.merge_schemas(schema1, schema2)

        self.assertIn("properties", merged)
        properties = merged["properties"]

        # Should have all fields from both schemas
        self.assertIn("id", properties)
        self.assertIn("name", properties)
        self.assertIn("email", properties)

        self.assertEqual(len(properties), 3)

    def test_api_response_with_data_array(self):
        """Test API response with data array structure"""
        test_data = {
            "status": "success",
            "data": [
                {"id": 1, "name": "John", "email": "john@example.com"},
                {
                    "id": 2,
                    "name": "Jane",
                    "role": "admin",  # This field only exists in second record
                },
            ],
            "meta": {"total": 2, "page": 1},
        }

        schema = self.converter.analyze_all_records(test_data)

        # Should capture all fields from all records
        self.assertIn("properties", schema)

        # Check if we have both root level and data array fields
        # The schema should include fields from the data array records
        properties = schema["properties"]

        # Should have root level fields
        self.assertIn("status", properties)
        self.assertIn("data", properties)
        self.assertIn("meta", properties)

    def test_count_records(self):
        """Test record counting functionality"""
        # Test with API response structure
        api_response = {"data": [{"id": 1}, {"id": 2}, {"id": 3}], "meta": {"total": 3}}
        count = self.converter.count_records(api_response)
        self.assertEqual(count, 4)  # 1 root + 3 data records

        # Test with direct array
        array_data = [{"id": 1}, {"id": 2}]
        count = self.converter.count_records(array_data)
        self.assertEqual(count, 2)

        # Test with single object
        single_object = {"id": 1, "name": "test"}
        count = self.converter.count_records(single_object)
        self.assertEqual(count, 1)

    def test_type_mapping(self):
        """Test Python type to schema type mapping"""
        test_cases = [
            (True, "boolean"),
            (False, "boolean"),
            (42, "integer"),
            (3.14, "number"),
            ("hello", "string"),
            (None, "null"),
        ]

        for value, expected_type in test_cases:
            with self.subTest(value=value):
                result_type = self.converter.get_type_from_value(value)
                self.assertEqual(result_type, expected_type)

    def test_empty_arrays(self):
        """Test handling of empty arrays"""
        test_data = {"empty_list": [], "items": ["item1", "item2"]}

        schema = self.converter.generate_schema_from_json(test_data)
        properties = schema["properties"]

        # Empty array should default to string items
        self.assertEqual(properties["empty_list"]["type"], "array")
        self.assertEqual(properties["empty_list"]["items"]["type"], "string")

        # Non-empty array should detect correct type
        self.assertEqual(properties["items"]["type"], "array")
        self.assertEqual(properties["items"]["items"]["type"], "string")


class TestJSONSamples(unittest.TestCase):
    """Test with sample JSON files"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.converter = JSONToYAMLConverter(self.temp_dir)
        self.sample_dir = Path(self.temp_dir) / "sample_data"

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_sample_files(self):
        """Create sample JSON files for testing"""
        # Simple API response
        test_api_response = {
            "status": "success",
            "data": [
                {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john@example.com",
                    "created_at": "2024-01-15T10:30:00Z",
                    "last_login": 1642248600,
                    "is_active": True,
                },
                {
                    "id": 2,
                    "username": "jane_smith",
                    "email": "jane@example.com",
                    "created_at": "2024-01-16T14:20:00.123Z",
                    "profile": {"first_name": "Jane", "last_name": "Smith"},
                    "is_active": False,
                },
            ],
            "pagination": {
                "current_page": 1,
                "total_pages": 5,
                "per_page": 2,
                "total_count": 10,
            },
        }

        # Complex nested structure
        complex_nested = {
            "company": {
                "id": 12345,
                "name": "Tech Corp",
                "founded_date": "2020-01-15",
                "headquarters": {
                    "address": {
                        "street": "123 Main St",
                        "city": "San Francisco",
                        "state": "CA",
                        "zip_code": "94105",
                        "coordinates": {"latitude": 37.7749, "longitude": -122.4194},
                    },
                    "phone": "+1-555-123-4567",
                },
                "departments": [
                    {
                        "id": 1,
                        "name": "Engineering",
                        "head": {
                            "employee_id": 101,
                            "name": "Alice Johnson",
                            "hire_date": "2020-03-15T09:00:00Z",
                        },
                        "employees": [
                            {
                                "id": 102,
                                "name": "Bob Wilson",
                                "position": "Senior Developer",
                                "salary": 120000,
                                "skills": ["Python", "JavaScript", "Go"],
                                "start_date": "2021-06-01T08:00:00Z",
                            },
                            {
                                "id": 103,
                                "name": "Carol Davis",
                                "position": "DevOps Engineer",
                                "salary": 110000,
                                "skills": ["Docker", "Kubernetes", "AWS"],
                                "certifications": [
                                    {
                                        "name": "AWS Solutions Architect",
                                        "issued_date": "2023-05-15",
                                        "expiry_date": "2026-05-15",
                                        "certificate_id": "AWS-SA-123456",
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "id": 2,
                        "name": "Marketing",
                        "head": {
                            "employee_id": 201,
                            "name": "David Brown",
                            "hire_date": "2020-05-20T10:30:00Z",
                        },
                        "budget": 500000.50,
                        "campaigns": [
                            {
                                "id": "campaign_001",
                                "name": "Q1 Product Launch",
                                "start_date": "2024-01-01",
                                "end_date": "2024-03-31",
                                "metrics": {
                                    "impressions": 1000000,
                                    "clicks": 25000,
                                    "conversions": 500,
                                    "cost_per_click": 2.5,
                                    "return_on_ad_spend": 4.2,
                                },
                            }
                        ],
                    },
                ],
                "financial_data": {
                    "revenue": {"q1_2024": 2500000.00, "q2_2024": 2750000.00},
                    "expenses": {
                        "operational": 1800000.00,
                        "marketing": 300000.00,
                        "r_and_d": 400000.00,
                    },
                    "last_updated": "2024-07-15T16:45:00Z",
                },
            }
        }

        # Write sample files
        self.sample_dir.mkdir(exist_ok=True)

        with open(self.sample_dir / "test_api_response.json", "w") as f:
            json.dump(test_api_response, f, indent=2)

        with open(self.sample_dir / "complex_nested.json", "w") as f:
            json.dump(complex_nested, f, indent=2)

    def test_sample_files_conversion(self):
        """Test conversion of sample files"""
        self.create_sample_files()

        # Process all files
        processed = self.converter.process_all_json_files()

        # Should have processed both files
        self.assertEqual(len(processed), 2)
        self.assertIn("test_api_response.yaml", processed)
        self.assertIn("complex_nested.yaml", processed)

        # Check output files exist
        yaml_output_dir = Path(self.temp_dir) / "yaml_output"
        self.assertTrue((yaml_output_dir / "test_api_response.yaml").exists())
        self.assertTrue((yaml_output_dir / "complex_nested.yaml").exists())

    def test_complex_nested_structure(self):
        """Test handling of deeply nested structures"""
        self.create_sample_files()

        # Read complex nested file
        with open(self.sample_dir / "complex_nested.json", "r") as f:
            data = json.load(f)

        # Generate schema
        schema = self.converter.analyze_all_records(data)

        # Verify deep nesting is handled
        self.assertIn("properties", schema)
        company_props = schema["properties"]["company"]["properties"]

        # Check nested address
        hq_props = company_props["headquarters"]["properties"]
        address_props = hq_props["address"]["properties"]
        self.assertIn("coordinates", address_props)

        # Check arrays within nested objects
        dept_props = company_props["departments"]["items"]["properties"]
        self.assertIn("employees", dept_props)

        employee_props = dept_props["employees"]["items"]["properties"]
        self.assertIn("skills", employee_props)
        self.assertEqual(employee_props["skills"]["type"], "array")


if __name__ == "__main__":
    unittest.main()
