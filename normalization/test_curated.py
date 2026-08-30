"""Validator rules: each test is the smallest thing that fails if the rule breaks.

Run: .venv/bin/python -m pytest test_curated.py -q   (or python test_curated.py)
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from codice_normalization.curated import load_dir

TYPES = "node_types:\n  - {key: poder, name: Poder}\n  - {key: poblacion, name: Población}\n"
OK_NODE = """
  - id: {id}
    node_type: poder
    name: Nodo {id}
    level: federal
    legal_basis:
      - document: CPEUM
        article: "Art. 1"
        url: https://www.diputados.gob.mx/LeyesBiblio/pdf/CPEUM.pdf
"""


def run(yaml_body: str, territories: set[str] | None = None):
    with TemporaryDirectory() as td:
        root = Path(td)
        (root / "node-types.yaml").write_text(TYPES)
        (root / "nodes").mkdir()
        (root / "nodes" / "t.yaml").write_text(yaml_body)
        return load_dir(root, territories)


def test_valid_minimal():
    g = run("nodes:" + OK_NODE.format(id="a"))
    assert g.ok, g.errors
    assert "a" in g.nodes


def test_duplicate_id():
    g = run("nodes:" + OK_NODE.format(id="a") + OK_NODE.format(id="a"))
    assert any("duplicate" in e for e in g.errors)


def test_missing_legal_basis():
    g = run("nodes:\n  - {id: a, node_type: poder, name: A, level: federal}")
    assert any("legal_basis" in e for e in g.errors)


def test_unknown_edge_ref():
    g = run("nodes:" + OK_NODE.format(id="a") + "edges:\n  - {from: a, to: fantasma, type: autoridad}")
    assert any("unknown node 'fantasma'" in e for e in g.errors)


def test_authority_cycle():
    body = (
        "nodes:" + OK_NODE.format(id="a") + OK_NODE.format(id="b")
        + "edges:\n  - {from: a, to: b, type: autoridad}\n  - {from: b, to: a, type: autoridad}"
    )
    g = run(body)
    assert any("cycle" in e for e in g.errors)


def test_bad_territory():
    body = "nodes:" + OK_NODE.format(id="a").replace("level: federal", "level: estatal\n    territory: '99'")
    g = run(body, territories={"01", "09"})
    assert any("INEGI" in e for e in g.errors)


def test_extinct_needs_valid_to_after_from():
    body = "nodes:" + OK_NODE.format(id="a").replace(
        "level: federal", "level: federal\n    valid_from: 2020-01-01\n    valid_to: 2019-01-01"
    )
    g = run(body)
    assert any("valid_to" in e for e in g.errors)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok {name}")
