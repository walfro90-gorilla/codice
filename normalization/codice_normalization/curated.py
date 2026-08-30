"""Load and validate hand-curated node YAML files (Fase 1).

The YAML files in /data/nodes are the source of truth for constitutional
structure. Validation happens HERE, at the layer boundary: anything invalid
stops before touching Postgres.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml
from codice_contracts import Edge, EdgeType, LegalBasis, Node
from pydantic import ValidationError

DEFAULT_VALID_FROM = date(1900, 1, 1)


@dataclass
class CuratedGraph:
    nodes: dict[str, Node] = field(default_factory=dict)
    node_types: dict[str, str] = field(default_factory=dict)  # node id -> type key
    edges: list[Edge] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _as_date(value, fallback: date | None) -> date | None:
    if value is None:
        return fallback
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def load_dir(data_dir: Path, known_territories: set[str] | None = None) -> CuratedGraph:
    """Parse every data/nodes/*.yaml; collect all errors instead of failing fast."""
    g = CuratedGraph()
    types_file = data_dir / "node-types.yaml"
    type_keys: set[str] = set()
    if types_file.exists():
        for t in yaml.safe_load(types_file.read_text())["node_types"]:
            type_keys.add(t["key"])
    else:
        g.errors.append(f"missing {types_file}")

    files = sorted((data_dir / "nodes").glob("*.yaml"))
    if not files:
        g.errors.append(f"no YAML files under {data_dir / 'nodes'}")

    raw_edges: list[tuple[str, dict]] = []
    for f in files:
        try:
            doc = yaml.safe_load(f.read_text()) or {}
        except yaml.YAMLError as e:
            g.errors.append(f"{f.name}: YAML parse error: {e}")
            continue
        for n in doc.get("nodes", []):
            where = f"{f.name}:{n.get('id', '?')}"
            try:
                node = Node(
                    id=n["id"],
                    node_type=n["node_type"],
                    name=n["name"],
                    level=n["level"],
                    territory_key=n.get("territory"),
                    summary=n.get("summary"),
                    legal_basis=[LegalBasis(**b) for b in n.get("legal_basis", [])],
                    valid_from=_as_date(n.get("valid_from"), DEFAULT_VALID_FROM),
                    valid_to=_as_date(n.get("valid_to"), None),
                )
            except (ValidationError, KeyError, TypeError, ValueError) as e:
                g.errors.append(f"{where}: {e}")
                continue
            if node.id in g.nodes:
                g.errors.append(f"{where}: duplicate id")
                continue
            if not node.legal_basis:
                g.errors.append(f"{where}: legal_basis is mandatory (R1)")
            if node.node_type not in type_keys:
                g.errors.append(f"{where}: unknown node_type {node.node_type!r}")
            if node.valid_to and node.valid_to <= node.valid_from:
                g.errors.append(f"{where}: valid_to must be after valid_from")
            g.nodes[node.id] = node
            g.node_types[node.id] = node.node_type
            parent = n.get("authority_from")
            if parent:
                raw_edges.append((where, {"from": parent, "to": node.id, "type": "autoridad"}))
        for e in doc.get("edges", []):
            raw_edges.append((f.name, e))

    for where, e in raw_edges:
        try:
            edge = Edge(
                from_node=e["from"],
                to_node=e["to"],
                type=EdgeType(e["type"]),
                legal_basis=e.get("legal_basis"),
                valid_from=_as_date(e.get("valid_from"), DEFAULT_VALID_FROM),
                valid_to=_as_date(e.get("valid_to"), None),
            )
        except (ValidationError, KeyError, ValueError) as e2:
            g.errors.append(f"{where}: bad edge: {e2}")
            continue
        for ref in (edge.from_node, edge.to_node):
            if ref not in g.nodes:
                g.errors.append(f"{where}: edge references unknown node {ref!r}")
        g.edges.append(edge)

    if known_territories is not None:
        for node in g.nodes.values():
            if node.territory_key and node.territory_key not in known_territories:
                g.errors.append(f"{node.id}: unknown INEGI key {node.territory_key!r} (R7)")

    _check_authority_dag(g)
    return g


def _check_authority_dag(g: CuratedGraph) -> None:
    """Authority edges must form a DAG (currently-valid ones)."""
    children: dict[str, list[str]] = {}
    for e in g.edges:
        if e.type == EdgeType.autoridad and e.valid_to is None:
            children.setdefault(e.from_node, []).append(e.to_node)
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {}

    def visit(u: str, path: list[str]) -> None:
        color[u] = GRAY
        for v in children.get(u, []):
            if color.get(v, WHITE) == GRAY:
                g.errors.append(f"authority cycle: {' -> '.join(path + [u, v])}")
            elif color.get(v, WHITE) == WHITE:
                visit(v, path + [u])
        color[u] = BLACK

    for u in list(g.nodes):
        if color.get(u, WHITE) == WHITE:
            visit(u, [])
