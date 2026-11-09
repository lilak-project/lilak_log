"""GET (GANIL DAQ) .xcfg files — the source table, as written.

    <Node id="CoBo">                          Node[CoBo]                     group
      <Instance id="*">                       Node[CoBo]/Instance[*]         group
        <!-- Number of time buckets. -->        (the next element's comment)
        <readoutDepth unit="buckets" range="[0, 512]">512</readoutDepth>
                                              …/Module/readoutDepth = 512   value
      <Revision id="5" include="x.xcfg" />    …/Revision[5]                  key

A path is the element names under the root, `[id]` where there is one; a
sibling repeating a name with no id gets `#2`, `#3`… `*` stays `*`: resolving
it (what each real channel gets) is the applied table's job, not this one's.

Every row keeps the stretch of text it was read from (`raw`, from the end of
the row before), so the rows put together are the file, byte for byte, and a
changed value is written back into its place.
"""
import re

TOKEN = re.compile(r"<!--.*?-->|<\?.*?\?>|<![^>]*>|</[^>]*>|<[^>]*>", re.S)
ATTR = re.compile(r'([A-Za-z_:][\w:.-]*)\s*=\s*"([^"]*)"')
META = ("id", "range", "unit", "type")


def _tag(tok: str):
    """(name, attrs, empty) of a start or empty tag."""
    body = tok[1:-1].strip()
    empty = body.endswith("/")
    body = body.rstrip("/").strip()
    name = body.split(None, 1)[0] if body else ""
    return name, dict(ATTR.findall(body)), empty


def parse(text: str) -> list:
    rows = []
    cut = 0                       # where the next row's raw starts
    comments = []                 # [(pos, text)] not yet given to an element
    stack = []                    # open elements: {name, seg, path, start, end, kids, row, counts}
    counts_root = {}

    def line_of(pos):
        return text.count("\n", 0, pos) + 1

    def take_comments(before):
        mine = [c for p, c in comments if p < before]
        comments[:] = [(p, c) for p, c in comments if p >= before]
        return " ".join(" ".join(c.split()) for c in mine)

    def emit(kind, upto, el, **kw):
        nonlocal cut
        row = {"path": el["path"] if el else "", "value": "", "comment": take_comments(el["start"]) if el else "",
               "kind": kind, "line": line_of(el["start"]) if el else line_of(cut), "raw": text[cut:upto], "span": None,
               "unit": (el or {}).get("attrs", {}).get("unit", ""), "range": (el or {}).get("attrs", {}).get("range", "")}
        row.update(kw)
        rows.append(row)
        cut = upto

    def open_el(m, name, attrs):
        parent = stack[-1] if stack else None
        if parent is not None and parent["row"] is None and len(stack) > 1:
            emit("group", parent["end"], parent)          # it holds elements: a group
            parent["row"] = len(rows) - 1
        if parent is not None:
            parent["kids"] += 1
        seg = f"{name}[{attrs['id']}]" if "id" in attrs else name
        counts = parent["counts"] if parent else counts_root
        counts[seg] = counts.get(seg, 0) + 1
        if counts[seg] > 1:
            seg = f"{seg}#{counts[seg]}"
        # The root (<Setup>) is left out of paths: every file has one.
        path = "/".join([e["seg"] for e in stack[1:]] + [seg]) if stack else ""
        return {"name": name, "seg": seg, "path": path, "attrs": attrs, "start": m.start(), "end": m.end(),
                "kids": 0, "row": None, "counts": {}}

    for m in TOKEN.finditer(text):
        tok = m.group(0)
        if tok.startswith("<!--"):
            comments.append((m.start(), tok[4:-3]))
        elif tok.startswith("<?") or tok.startswith("<!"):
            pass
        elif tok.startswith("</"):
            el = stack.pop() if stack else None
            if el is None:
                continue
            if el["kids"] == 0 and stack:
                inner = text[el["end"]:m.start()]
                lead = len(inner) - len(inner.lstrip())
                value = inner.strip()
                s = el["end"] + lead - cut
                emit("value", m.end(), el, value=value, span=[s, s + len(value)])
            elif not stack:
                emit("root", m.end(), el)
        else:
            name, attrs, empty = _tag(tok)
            el = open_el(m, name, attrs)
            if empty:
                extra = " ".join(f"{k}={v}" for k, v in attrs.items() if k not in META)
                emit("key", m.end(), el, value=extra)
            else:
                stack.append(el)
    if cut < len(text):
        rows.append({"path": "", "value": "", "comment": take_comments(len(text) + 1), "kind": "blank",
                     "line": line_of(cut), "raw": text[cut:], "span": None, "unit": "", "range": ""})
    return rows


def render(rows: list) -> str:
    out = []
    for r in rows:
        raw, span = r["raw"], r.get("span")
        if span and raw[span[0]:span[1]] != r["value"]:
            raw = raw[:span[0]] + r["value"] + raw[span[1]:]
        out.append(raw)
    return "".join(out)
