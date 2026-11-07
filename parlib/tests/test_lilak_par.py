"""parlib checks: python3 tests/test_lilak_par.py [lilak checkout to round-trip]."""
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
print("OK")
