"""Offline tests for industry_map_client (no network).

Validates the consumer client against the real published artifact
(out/industry_data.json) and the two historical on-disk cache shapes, using
auto_refresh=False (cache-only) so no network is touched.
"""

import json
from pathlib import Path

import pytest

from industry_map_client import IndustryMap
from industry_map_client.client import DEFAULT_METADATA

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = REPO_ROOT / "out" / "industry_data.json"


def _seed_cache(path: Path, shape: str = "full") -> None:
    """Write a cache file from the real artifact in one of the legacy shapes."""
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    if shape == "full":  # nse-corporate-data / FirstFilingsIN / IndiaInc shape
        out = {"metadata": payload["metadata"], "data": payload["data"], "etag": '"abc123"'}
    elif shape == "surveillance":  # {"etag","data"} — no metadata key
        out = {"etag": '"abc123"', "data": payload["data"]}
    else:
        raise ValueError(shape)
    path.write_text(json.dumps(out), encoding="utf-8")


@pytest.fixture()
def cache_path(tmp_path):
    return tmp_path / "industry_cache.json"


def test_lookup_known_symbol(cache_path):
    _seed_cache(cache_path)
    im = IndustryMap(cache_path=cache_path, auto_refresh=False)
    assert im.industry("ABB") == "Heavy Electrical Equipment"
    assert im.levels("ABB") == [
        "Industrials",
        "Capital Goods",
        "Electrical Equipment",
        "Heavy Electrical Equipment",
    ]


def test_classify_maps_levels_to_names(cache_path):
    _seed_cache(cache_path)
    im = IndustryMap(cache_path=cache_path, auto_refresh=False)
    c = im.classify("ABB")
    assert c == {
        "Macro": "Industrials",
        "Sector": "Capital Goods",
        "Industry": "Electrical Equipment",
        "Basic Industry": "Heavy Electrical Equipment",
    }


def test_symbol_normalization(cache_path):
    _seed_cache(cache_path)
    im = IndustryMap(cache_path=cache_path, auto_refresh=False)
    assert im.industry("  abb ") == im.industry("ABB")


def test_unknown_symbol_returns_none(cache_path):
    _seed_cache(cache_path)
    im = IndustryMap(cache_path=cache_path, auto_refresh=False)
    assert im.industry("NOTAREALSYMBOL") is None
    assert im.levels("") is None
    assert im.industry(None) is None


def test_surveillance_cache_shape_without_metadata(cache_path):
    _seed_cache(cache_path, shape="surveillance")
    im = IndustryMap(cache_path=cache_path, auto_refresh=False)
    # Falls back to canonical metadata; data still usable.
    assert im.metadata == DEFAULT_METADATA
    assert im.industry("ABB") == "Heavy Electrical Equipment"


def test_payload_shape(cache_path):
    _seed_cache(cache_path)
    im = IndustryMap(cache_path=cache_path, auto_refresh=False)
    payload = im.as_payload()
    assert set(payload) == {"metadata", "data"}
    assert isinstance(payload["data"], dict) and payload["data"]


def test_corrupt_cache_is_not_fatal(cache_path):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("{not valid json", encoding="utf-8")
    im = IndustryMap(cache_path=cache_path, auto_refresh=False)
    assert im.data == {}
    assert im.industry("ABB") is None


def test_missing_cache_no_network_is_empty(tmp_path):
    im = IndustryMap(cache_path=tmp_path / "nope.json", auto_refresh=False)
    assert im.data == {}
