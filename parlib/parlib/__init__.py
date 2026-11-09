"""Parameter files as tables, and back.

Every format is a pair: parse(text) -> rows, render(rows) -> text, and passes
when render(parse(text)) == text. A row is

    {path, value, comment, kind, line, raw, span}

kind: "value" (a parameter), "key" (a name with no value), "group" (a header
that prefixes what is indented under it), "comment", "blank". `raw` is the line
as written and `span` where its value sits in it, so a row whose value was
changed is rendered by putting the new value in that place: spacing, comments
and order stay as they were.

Nothing here knows about rack or the portal: the same code can move to the
platform the prototype is for.
"""
import hashlib

from . import lilak_par, xcfg

FORMATS = {"lilak-par": lilak_par, "get-xcfg": xcfg}


def parse(text: str, fmt: str) -> list | None:
    """Rows of `text`, or None when `fmt` has no parser (kept as text only)."""
    m = FORMATS.get(fmt)
    return m.parse(text) if m else None


def render(rows: list, fmt: str) -> str:
    return FORMATS[fmt].render(rows)


def text_hash(text: str) -> str:
    """The text exactly as written."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def value_hash(rows: list) -> str:
    """The values only: `path=value` pairs, sorted — comments, spacing and line
    order do not count, so two files saying the same thing are the same set."""
    pairs = sorted(f"{r['path']}={r['value']}" for r in rows if r["kind"] in ("value", "key"))
    return hashlib.sha256("\n".join(pairs).encode("utf-8")).hexdigest()


def hashes(text: str, fmt: str) -> dict:
    """{text_hash, value_hash, count}: value_hash falls back to the text's when
    the format has no parser."""
    rows = parse(text, fmt)
    th = text_hash(text)
    if rows is None:
        return {"text_hash": th, "value_hash": th, "count": None}
    return {"text_hash": th, "value_hash": value_hash(rows),
            "count": sum(1 for r in rows if r["kind"] in ("value", "key"))}
