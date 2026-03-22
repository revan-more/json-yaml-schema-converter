# Publishing `json_yaml_schema` to PyPI

Follow these instructions to publish new updates of the package to PyPI.

---

### Step 1: Update the Version Number
PyPI does not allow you to overwrite or republish an existing version of a package. You must increment the version before publishing. 
Open `setup.py` and increment your version (e.g., from `0.1.0` to `0.2.0`):
```python
    name="json_yaml_schema",
    version="0.2.0", # <-- Bump this version
```

### Step 2: Install Build Tools
Make sure you have the latest versions of standard Python packaging tools installed:
```bash
pip install --upgrade setuptools wheel build twine
```

### Step 3: Clean Previous Builds (Recommended)
Remove the old `dist/` and `build/` folders so you don't accidentally upload older versions of your package instead of the new one.
```bash
rm -rf dist/ build/ *.egg-info/
```

### Step 4: Build the Package
Run the following command in the same directory as your `setup.py`. This creates a Source Distribution (`.tar.gz`) and a Built Distribution (`.whl`) inside the `dist/` directory.
```bash
python -m build
```
*(Alternative for older environments: `python setup.py sdist bdist_wheel`)*

### Step 5: Verify the Build
Check that the newly generated files in `dist/` do not contain any errors (like a missing long description or invalid classifiers):
```bash
twine check dist/*
```

### Step 6: Upload the Package to PyPI
Finally, upload the new distribution files:
```bash
twine upload dist/*
```
- It will prompt you for a **username** and **password**.
- **Username:** `__token__` (Yes, literally enter the text `__token__` if using an API token).
- **Password:** Paste your API token from PyPI (it begins with `pypi-`).

*Note: If you don't have an API token yet, log in to [pypi.org](https://pypi.org/), go to **Account settings**, scroll down to **API tokens**, and click "Add API token".*

---

## (Optional) Test Run on TestPyPI
If you wish to test out publishing before pushing to the real PyPI servers, you can upload to the TestPyPI repository:
```bash
twine upload --repository testpypi dist/*
```