"""parameters backend — parameter sets, one shared document per portal project.

A set is one tool's parameters in one format (lilak-par, …), reused by every
run that used exactly those values; logbook's logs point at the sets they ran
with. The parsing is parlib's (lilak_log/parlib), which knows nothing of rack.

Besides the rack document and the files:

    POST /api/register?title=&format=&name=&origin=   body = the parameter text.
         Parsed and hashed; a set with the same values (value_hash, same
         format) is answered instead of making a new one: {record, existing}.
         With `name` the text is kept as a file of the set, else in its `text`.
    GET  /api/table?id=   the set's rows, parsed from its text or first file.

Hashes are made here and only here, so a set is registered through
/api/register (the page's register tab, scripts, MCP); its text and files are
not edited in the form.
"""
import copy
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import parlib
from fastapi import Depends, FastAPI, HTTPException, Request
from lilak_portal_auth import signed_in

from rackstore.store import Document, mount_spa, mount_uploads

DATA = Path(os.environ.get("PARAMETERS_DATA_DIR", "./data"))
PROJECT = os.environ.get("PORTAL_PROJECT", "")
DIST = Path(os.environ.get("PARAMETERS_DIST_DIR", "./dist"))
UPLOADS = DATA / "uploads"
TEXT_CAP = 64 * 1024          # longer than this is kept as a file, not in the record
FILE_CAP = 50 * 1024 * 1024

DOC = Document(DATA / "data.json", keys=("sets", "settings"), keep_days=30)

app = FastAPI(title="parameters")
DOC.mount(app, project=PROJECT)
mount_uploads(app, UPLOADS)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _who(me: dict) -> str:
    return me.get("email") or me.get("username") or ""


def _content(rec: dict) -> str:
    """A set's text: its own, else its first file's."""
    if rec.get("text"):
        return rec["text"]
    for f in rec.get("files") or []:
        p = (UPLOADS / str(f.get("id", "")) / str(f.get("name", ""))).resolve()
        if p.is_relative_to(UPLOADS.resolve()) and p.is_file():
            return p.read_text(encoding="utf-8", errors="replace")
    return ""


def _save_file(name: str, body: bytes, me: dict) -> dict:
    """The file as mount_uploads keeps one: uploads/<id>/<name>."""
    clean = "".join(c for c in Path(name).name if c not in '\\/:*?"<>|\x00').strip().lstrip(".")[:180] or "parameters.txt"
    uid = uuid.uuid4().hex[:12]
    p = UPLOADS / uid / clean
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(body)
    return {"id": uid, "name": clean, "size": len(body), "type": "text/plain", "at": _now(), "by": _who(me)}


@app.post("/api/register")
async def register(request: Request, title: str = "", format: str = "lilak-par", name: str = "",
                   origin: str = "person", me: dict = Depends(signed_in)) -> dict:
    body = await request.body()
    if not body.strip():
        raise HTTPException(400, "빈 내용입니다.")
    if len(body) > FILE_CAP:
        raise HTTPException(413, "파일은 50MB까지입니다.")
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "UTF-8 텍스트가 아닙니다.")
    if not name and len(body) > TEXT_CAP:
        raise HTTPException(413, "64KB보다 긴 내용은 파일 이름(name)과 함께 올려 주세요.")
    h = parlib.hashes(text, format)
    with DOC.lock:
        cur = DOC.read()
        same = next((r for r in cur.get("sets") or []
                     if r.get("value_hash") == h["value_hash"] and r.get("format") == format), None)
        if same:
            return {"record": same, "existing": True}
        now = _now()
        rec = {"id": str(uuid.uuid4()), "createdAt": now, "updatedAt": now,
               "title": title.strip() or (Path(name).name if name else "") or h["value_hash"][:8],
               "format": format, "origin": origin if origin in ("auto", "person", "llm") else "person",
               "status": "trial", "author": _who(me), **h}
        if name:
            rec["files"] = [_save_file(name, body, me)]
        else:
            rec["text"] = text
        new = copy.deepcopy(cur)
        new["sets"] = [rec] + list(new.get("sets") or [])
        DOC.write(new, _who(me), replaces=cur)
    return {"record": rec, "existing": False}


@app.get("/api/table")
def table(id: str, _: dict = Depends(signed_in)) -> dict:
    rec = next((r for r in DOC.read().get("sets") or [] if str(r.get("id")) == id), None)
    if rec is None:
        raise HTTPException(404, "그 묶음이 없습니다.")
    rows = parlib.parse(_content(rec), rec.get("format") or "")
    # Only what the table shows: raw/span are for render and double the payload.
    keep = ("line", "path", "value", "unit", "range", "comment")
    rows = rows and [{k: r[k] for k in keep if r.get(k) not in (None, "")}
                     for r in rows if r.get("kind") in ("value", "key")]
    return {"format": rec.get("format"), "rows": rows}


# Must stay last: the catch-all would shadow /api/*.
mount_spa(app, DIST, name="parameters")
