"""parameters backend checks: python3 test_parameters.py (portal venv)."""
import os
import sys
import tempfile
from pathlib import Path

os.environ["PARAMETERS_DATA_DIR"] = tempfile.mkdtemp()
sys.path.insert(0, str(Path(__file__).parent))
from fastapi.testclient import TestClient  # noqa: E402
from lilak_portal_auth import signed_in  # noqa: E402

import main  # noqa: E402

main.app.dependency_overrides[signed_in] = lambda: {"email": "t@x"}
c = TestClient(main.app)

r = c.post("/api/register?title=A&format=lilak-par", content="a 1 # one\nb 2\n").json()
assert not r["existing"] and r["record"]["count"] == 2 and r["record"]["text"]
first = r["record"]["id"]
# Same values, other comments and order: the same set comes back, nothing new.
r = c.post("/api/register?title=B&format=lilak-par", content="# x\nb 2\na 1\n").json()
assert r["existing"] and r["record"]["id"] == first
# Other values: a new set.
r = c.post("/api/register?title=C&format=lilak-par", content="a 1\nb 3\n").json()
assert not r["existing"]
# Kept as a file, and the table is read from it.
r = c.post("/api/register?format=lilak-par&name=run.par", content="g/\n    x 5\n").json()
assert r["record"]["files"][0]["name"] == "run.par" and "text" not in r["record"] and r["record"]["title"] == "run.par"
t = c.get(f"/api/table?id={r['record']['id']}").json()
assert [(x["path"], x["value"]) for x in t["rows"] if "value" in x] == [("g/x", "5")]
assert len(c.get("/api/data").json()["sets"]) == 3
assert c.post("/api/register", content="  ").status_code == 400
assert c.post("/api/register", content="x" * (65 * 1024)).status_code == 413
assert c.get("/api/table?id=nope").status_code == 404
print("OK")
