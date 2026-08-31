"""The rules that keep a person's name from being published without a source.

Every case here is a way the file could quietly publish something it should
not: a name with no document, two people holding one office, a holder of an
organ that no longer exists, a personal email.
"""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from codice_normalization.titulares import load_file

DOC = """
    nombramiento:
      documento: DOF — Acuerdo de nombramiento
      url: https://www.dof.gob.mx/nota_detalle.php?codigo=1234567
      fecha: 2024-10-01
"""


def run(body: str, nodes=None):
    with TemporaryDirectory() as td:
        p = Path(td) / "titulares.yaml"
        p.write_text(body)
        return load_file(p, nodes)


def test_a_valid_entry_loads():
    s = run(f"""titulares:
  - node: secretaria-hacienda
    nombre: Persona de Prueba
    cargo: Secretaria de Hacienda
    desde: 2024-10-01
{DOC}""")
    assert s.ok, s.errors
    assert s.holders[0].node_id == "secretaria-hacienda"
    assert s.holders[0].start_date == date(2024, 10, 1)


def test_a_name_without_a_document_is_refused():
    # The whole reason this module exists (R1).
    s = run("""titulares:
  - node: secretaria-hacienda
    nombre: Persona de Prueba
    cargo: Secretaria de Hacienda
    desde: 2024-10-01
""")
    assert not s.ok
    assert any("sin documento" in e for e in s.errors)
    assert s.holders == []


def test_two_holders_of_one_office_at_once_is_refused():
    s = run(f"""titulares:
  - node: secretaria-hacienda
    nombre: Primera Persona
    cargo: Secretaria
    desde: 2020-01-01
{DOC}
  - node: secretaria-hacienda
    nombre: Segunda Persona
    cargo: Secretario
    desde: 2024-10-01
{DOC}""")
    assert not s.ok
    assert any("al mismo tiempo" in e for e in s.errors)


def test_closing_the_previous_term_makes_the_pair_valid():
    s = run(f"""titulares:
  - node: secretaria-hacienda
    nombre: Primera Persona
    cargo: Secretaria
    desde: 2020-01-01
    hasta: 2024-09-30
{DOC}
  - node: secretaria-hacienda
    nombre: Segunda Persona
    cargo: Secretario
    desde: 2024-10-01
{DOC}""")
    assert s.ok, s.errors
    assert len(s.holders) == 2  # R9: the earlier one is kept, not deleted


def test_nobody_can_head_an_organ_that_was_already_abolished():
    nodes = {"inai": (date(2003, 1, 1), date(2025, 3, 20))}
    s = run(f"""titulares:
  - node: inai
    nombre: Persona de Prueba
    cargo: Comisionada
    desde: 2025-06-01
{DOC}""", nodes)
    assert not s.ok
    assert any("extinto" in e for e in s.errors)


def test_unknown_node_is_refused():
    s = run(f"""titulares:
  - node: secretaria-que-no-existe
    nombre: Persona de Prueba
    cargo: Titular
    desde: 2024-10-01
{DOC}""", {"secretaria-hacienda": (date(1900, 1, 1), None)})
    assert not s.ok
    assert any("no existe" in e for e in s.errors)


def test_personal_contact_is_dropped_and_reported():
    s = run(f"""titulares:
  - node: secretaria-hacienda
    nombre: Persona de Prueba
    cargo: Secretaria
    desde: 2024-10-01
    contacto: persona@gmail.com
{DOC}""")
    assert not s.ok
    assert any("institucional" in e for e in s.errors)


def test_an_empty_file_is_valid():
    # An empty curated file is honest; a half-sourced one is not.
    s = run("titulares: []")
    assert s.ok
    assert s.holders == []


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok {name}")
