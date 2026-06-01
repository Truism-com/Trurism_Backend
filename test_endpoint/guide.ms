# Install test dependencies (add to requirements-dev.txt)
pip install pytest pytest-asyncio httpx aiosqlite

# Run all tests
pytest test_endpoint/ -v

# Run only unit tests (fast, no DB)
pytest test_endpoint/ -v -k "schema or service or unit"

# Run with coverage report
pytest test_endpoint/ --cov=app --cov-report=term-missing

# Run a single file
pytest test_endpoint/test_auth.py -v