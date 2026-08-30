"""Amount formats change between PEF years; all must land on the same number."""

from codice_ingestion.pef import _amount


def test_amount_formats():
    assert _amount("11746796796246.00") == 11746796796246.00
    assert _amount("259,000,000.00") == 259000000.00   # older files use separators
    assert _amount("1,234") == 1234.0                  # thousands, not decimals
    assert _amount("1,5") == 1.5                       # decimal comma
    assert _amount("$1,000.50") == 1000.50


def test_accounting_zero_is_zero_not_a_failure():
    for token in ("", "-", "--", "N/A", "nd"):
        assert _amount(token) == 0.0, token
    assert _amount(None) == 0.0


def test_unreadable_returns_none_so_the_caller_can_count_it():
    # Coercing garbage to 0 is how a budget loses money without anyone noticing
    assert _amount("no aplica todavía") is None
    assert _amount("1.2.3.4") is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok {name}")
