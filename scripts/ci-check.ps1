$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip
pip install black flake8 pytest
black --check .
flake8
pytest -q
