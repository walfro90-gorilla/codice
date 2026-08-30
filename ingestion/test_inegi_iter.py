"""DMS coordinate conversion: smallest check that fails if parsing breaks."""

from codice_ingestion.inegi_iter import dms_to_decimal


def test_dms():
    assert abs(dms_to_decimal('102°17\'45.768" W') - (-102.29604666666667)) < 1e-9
    assert abs(dms_to_decimal('21°52\'47.362" N') - 21.879822777777776) < 1e-9
    assert dms_to_decimal("") is None
    assert dms_to_decimal('10°0\'0" O') == -10.0  # INEGI sometimes uses O for Oeste
    try:
        dms_to_decimal("garbage")
        raise AssertionError("should have raised")
    except ValueError:
        pass


if __name__ == "__main__":
    test_dms()
    print("ok test_dms")
