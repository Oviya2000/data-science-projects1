"""Unit smoke tests for every Lambda in the pipeline."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas"))
os.environ["USE_MOCK_WEATHER"] = "1"    # force deterministic mock

import fetch_weather
import validate
import transform
import load_partitioned


def test_fetch_returns_records():
    r = fetch_weather.handler({})
    assert r["run_id"]
    assert len(r["records"]) == 10
    assert all(-90 <= x["latitude"] <= 90 for x in r["records"])


def test_validate_drops_bad_rows():
    good = fetch_weather.handler({})["records"]
    bad = [{"city": "X"}]  # missing everything
    r = validate.handler({"records": good + bad, "run_id": "t"})
    assert r["valid_count"] == len(good)


def test_transform_adds_derived_fields():
    fetched = fetch_weather.handler({})
    tr = transform.handler({"records": fetched["records"], "run_id": "t"})
    r = tr["records"][0]
    assert "feels_like_c" in r
    assert "comfort_band" in r
    assert r["comfort_band"] in {"Freezing", "Cold", "Comfortable", "Warm", "Uncomfortable"}


def test_load_writes_partition_locally(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fetched = fetch_weather.handler({})
    tr = transform.handler(fetched)
    out = load_partitioned.handler(tr)
    assert out["loaded"] == 10
    written = Path(out["s3_uri"])
    assert written.exists()
    assert "year=" in str(written) and "month=" in str(written) and "day=" in str(written)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
