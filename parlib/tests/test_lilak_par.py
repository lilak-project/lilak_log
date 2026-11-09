"""parlib checks: python3 tests/test_lilak_par.py [lilak checkout] [folder of .xcfg] — each round-trips."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import parlib  # noqa: E402

SAMPLE = """# header
Isotropic/
    Particle               4He      # particle name
    EnergyLow              9.9  MeV
    Direction
LKRun/InputFile   {lilak_common}/run_{RUN}.root
group_db/groups/0/name "Ring-12 (dE)"
"""

rows = parlib.parse(SAMPLE, "lilak-par")
by = {r["path"]: r for r in rows if r["path"]}
assert by["Isotropic/Particle"]["value"] == "4He" and by["Isotropic/Particle"]["comment"] == "particle name"
assert by["Isotropic/EnergyLow"]["value"] == "9.9  MeV"
assert by["Isotropic/Direction"]["kind"] == "key"
assert by["LKRun/InputFile"]["value"] == "{lilak_common}/run_{RUN}.root"
assert by["group_db/groups/0/name"]["value"] == '"Ring-12 (dE)"'
assert parlib.render(rows, "lilak-par") == SAMPLE

# An edited value lands in its place; the rest of the line stays.
by["Isotropic/Particle"]["value"] = "1H"
assert "    Particle               1H      # particle name" in parlib.render(rows, "lilak-par")

# Same values, different comments and order → same value hash, different text hash.
a = "a 1 # one\nb 2\n"
b = "# note\nb 2\na 1\n"
ha, hb = parlib.hashes(a, "lilak-par"), parlib.hashes(b, "lilak-par")
assert ha["value_hash"] == hb["value_hash"] and ha["text_hash"] != hb["text_hash"]
assert parlib.hashes("a 2\nb 2\n", "lilak-par")["value_hash"] != ha["value_hash"]
assert parlib.parse("x", "manual") is None and parlib.hashes("x", "manual")["count"] is None

# GET xcfg: paths, ids, repeated siblings, comments, attributes; byte-for-byte back.
X = """<?xml version="1.0" encoding="UTF-8"?>
<Setup id="Conditions">
\t<!-- Parameters specific
\t     to GetController -->
\t<ECC>
\t\t<Verbose>true</Verbose>
\t</ECC>
\t<Node id="CoBo">
\t\t<Instance id="*">
\t\t\t<!-- Number of time buckets. -->
\t\t\t<readoutDepth unit="buckets" range="[0, 512]">512</readoutDepth>
\t\t\t<Reg>1</Reg>
\t\t\t<Reg>2</Reg>
\t\t\t<channel id="46" />
\t\t</Instance>
\t\t<Revision id="5" include="x.xcfg" />
\t</Node>
</Setup>
"""
rows = parlib.parse(X, "get-xcfg")
by = {r["path"]: r for r in rows if r["path"]}
assert by["ECC"]["kind"] == "group" and by["ECC"]["comment"] == "Parameters specific to GetController"
assert by["ECC/Verbose"]["value"] == "true"
d = by["Node[CoBo]/Instance[*]/readoutDepth"]
assert (d["value"], d["unit"], d["range"], d["comment"]) == ("512", "buckets", "[0, 512]", "Number of time buckets.")
assert by["Node[CoBo]/Instance[*]/Reg#2"]["value"] == "2"
assert by["Node[CoBo]/Instance[*]/channel[46]"]["kind"] == "key"
assert by["Node[CoBo]/Revision[5]"]["value"] == "include=x.xcfg"
assert parlib.render(rows, "get-xcfg") == X
d["value"] = "256"
assert '<readoutDepth unit="buckets" range="[0, 512]">256</readoutDepth>' in parlib.render(rows, "get-xcfg")

# Every parameter file of a LILAK checkout round-trips.
if len(sys.argv) > 1:
    n = 0
    for p in Path(sys.argv[1]).rglob("*"):
        if p.suffix in (".par", ".mac", ".conf") and p.is_file() and p.stat().st_size < 2_000_000:
            try:
                t = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            assert parlib.render(parlib.parse(t, "lilak-par"), "lilak-par") == t, p
            n += 1
    print(f"{n} files round-trip")
if len(sys.argv) > 2:
    xs = sorted(Path(sys.argv[2]).rglob("*.xcfg"))
    for p in xs:
        t = p.read_text(encoding="utf-8")
        rows = parlib.parse(t, "get-xcfg")
        assert parlib.render(rows, "get-xcfg") == t, p
        paths = [r["path"] for r in rows if r["kind"] in ("value", "key")]
        assert len(paths) == len(set(paths)), p
    print(f"{len(xs)} xcfg round-trip, paths unique")
print("OK")
