import pytest
from scripts.reproducible_time import generated_at_utc


def test_generated_at_utc_defaults_to_unix_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    assert generated_at_utc() == "1970-01-01T00:00:00+00:00"


def test_generated_at_utc_uses_declared_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "946684800")
    assert generated_at_utc() == "2000-01-01T00:00:00+00:00"


@pytest.mark.parametrize("value", ["not-an-integer", "-1"])
def test_generated_at_utc_rejects_invalid_epoch(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", value)
    with pytest.raises(ValueError, match="SOURCE_DATE_EPOCH"):
        generated_at_utc()
