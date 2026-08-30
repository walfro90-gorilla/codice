"""Name normalization and institutional-contact filtering.

Run: .venv/bin/python test_people.py
"""

from codice_normalization.people import normalize_name, _institutional


def test_normalize_strips_accents_and_punctuation():
    assert normalize_name("Álvarez Lima, José Antonio") == "alvarez lima jose antonio"
    # ñ collapses to n by design — official sources mangle it (see docstring)
    assert normalize_name("PEÑA  NIETO") == "pena nieto"
    assert normalize_name("O'Farrill-Smith") == "o farrill smith"


def test_normalize_is_stable_across_source_formats():
    # SITL lists "Apellido Apellido Nombre"; the profile gives "Nombre Apellido
    # Apellido". Normalizing does NOT reorder — same-person detection across
    # orderings is entity resolution's job, with a human in the loop (R3).
    listed = normalize_name("Acosta Trujillo Juana")
    profile = normalize_name("Juana Acosta Trujillo")
    assert listed != profile
    assert set(listed.split()) == set(profile.split())


def test_only_institutional_contact_is_kept():
    assert _institutional("juana.acosta@diputados.gob.mx") == "juana.acosta@diputados.gob.mx"
    assert _institutional("SEN.X@senado.gob.mx") == "sen.x@senado.gob.mx"
    assert _institutional("persona@gmail.com") is None
    assert _institutional(None) is None




def test_party_aliases_unify_across_chambers():
    from codice_normalization.people import canonical_party
    # The Chamber writes VERDE, the Senate PVEM — one key or no cross-chamber query.
    assert canonical_party("VERDE") == canonical_party("PVEM") == "PVEM"
    assert canonical_party("morena") == "MORENA"
    # "Sin Grupo" is the absence of a party, not a party (R6: say what we don't know)
    assert canonical_party("SG") is None
    assert canonical_party(None) is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok {name}")
