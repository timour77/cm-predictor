import sys
import os

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, os.path.normpath(backend_dir))

try:
    from main import app
except Exception as _import_err:
    from fastapi import FastAPI
    app = FastAPI()

    _err_str = str(_import_err)

    @app.get("/api/debug")
    @app.post("/api/debug")
    def debug():
        return {"import_error": _err_str, "python": sys.version, "path": sys.path[:5]}
