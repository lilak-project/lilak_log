"""LILAK parameter files (.par, .mac, .conf) — LKParameterContainer::AddLine's rules.

    # a comment line
    group/                       a header: what is indented under it is group/…
        name    value   # note   a parameter, its value and comment
        name                     a name with no value
    a/b/c   1 2 3                a full path on one line

Indentation is counted in spaces, as LILAK counts it. A value runs to the first
`#`; `{RUN}`-style substitutions are kept as written.
"""


def parse(text: str) -> list:
    rows = []
    groups = []                                  # [(indent, "path/")]
    for i, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip(" \t\r")
        body = line.lstrip(" ")
        indent = len(line) - len(body)
        row = {"path": "", "value": "", "comment": "", "kind": "", "line": i, "raw": raw, "span": None}
        if not body.strip():
            row["kind"] = "blank"
        elif body.startswith("#"):
            row.update(kind="comment", comment=body[1:].strip())
        else:
            while groups and groups[-1][0] >= indent:
                groups.pop()
            prefix = groups[-1][1] if groups else ""
            name = body.split()[0]
            at = indent + len(name)              # just past the name
            rest = line[at:]
            path = prefix + name
            if not rest.strip() or rest.lstrip().startswith("#"):
                row.update(path=path, comment=rest.strip()[1:].strip(),
                           kind="group" if name.endswith("/") else "key")
                if name.endswith("/"):
                    groups.append((indent, path))
            else:
                start = at + len(rest) - len(rest.lstrip())
                end = line.find("#", start)
                comment = ""
                if end >= 0:
                    comment = line[end + 1:].strip()
                else:
                    end = len(line)
                value = line[start:end].rstrip(" \t")
                row.update(path=path, value=value, comment=comment, kind="value",
                           span=[start, start + len(value)])
        rows.append(row)
    return rows


def render(rows: list) -> str:
    """The text back: each line as written, with its value replaced where the
    row's value is no longer what the line holds."""
    out = []
    for r in rows:
        raw, span = r["raw"], r.get("span")
        if span and raw[span[0]:span[1]] != r["value"]:
            raw = raw[:span[0]] + r["value"] + raw[span[1]:]
        out.append(raw)
    return "\n".join(out)
