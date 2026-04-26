import sys
import os

try:
    from app.main import app
    schema = app.openapi()
    print("OpenAPI schema generated successfully.")
except Exception as e:
    import traceback
    traceback.print_exc()
