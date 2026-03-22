from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(this_directory, "requirements.txt")) as f:
    requirements = f.read().splitlines()

setup(
    name="json_yaml_schema",
    version="0.2.0",
    author="Revan More",
    author_email="[EMAIL_ADDRESS]",
    description="""Convert JSON API responses to YAML schema
                with format with properties, types, and titles""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/revan-more/json_yaml_schema_converter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "json2yaml_schema=json_yaml_schema.cli:main",
            "json2yaml-mcp-server=json_yaml_schema.mcp_server:main",
        ],
    },
    keywords="json yaml schema converter api openapi swagger, mcp, mcp-server json-schema",
    project_urls={
        "Bug Reports": "https://github.com/revan-more/json_yaml_schema_converter/issues",
        "Source": "https://github.com/revan-more/json_yaml_schema_converter",
        "Documentation": "https://github.com/revan-more/json_yaml_schema_converter#readme",
    },
    include_package_data=True,
)
