from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="json-yaml-converter",
    version="0.1.0",
    author="Revan More",
    author_email="revanmore12@gmail.com",
    description="""Convert JSON API responses to YAML schema
                with format with properties, types, and titles""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/revan-more/json-yaml-schema-converter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "json2yaml-schema=json_yaml_schema_converter.cli:main",
        ],
    },
    keywords="json yaml schema converter api openapi swagger",
    project_urls={
        "Bug Reports": "https://github.com/revan-more/json-yaml-schema-converter/issues",
        "Source": "https://github.com/revan-more/json-yaml-schema-converter",
        "Documentation": "https://github.com/revan-more/json-yaml-schema-converter#readme",
    },
    include_package_data=True,
)