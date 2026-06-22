"""ETag-cached consumer client for the published industry-data artifact.

Stdlib-only (no third-party runtime deps). See package docstring for rationale.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError

logger = logging.getLogger(__name__)

DEFAULT_URL = (
    "https://raw.githubusercontent.com/eggmasonvalue/"
    "stock-industry-map-in/main/out/industry_data.json"
)
DEFAULT_CACHE_PATH = Path.home() / ".industry_map_in" / "industry_cache.json"

# Canonical level names (mirrors src/store.py in the producer).
DEFAULT_METADATA: List[str] = ["Macro", "Sector", "Industry", "Basic Industry"]


class IndustryMap:
    """Lazy, ETag-cached view over the published industry-data artifact.

    The first access (any of :meth:`data`, :meth:`get`, :meth:`industry`, ...)
    triggers a single conditional fetch and caches the result both on disk and
    in memory. Subsequent accesses are served from memory until
    :meth:`refresh` is called.

    Args:
        cache_path: Local cache file. Defaults to
            ``~/.industry_map_in/industry_cache.json``. Apps migrating from a
            bespoke cache may point this at their old path for byte-for-byte
            continuity (e.g. ``~/.first_filings/industry_cache.json``).
        url: Source artifact URL. Defaults to the GitHub-raw published file.
        timeout: HTTP timeout in seconds.
        auto_refresh: If True (default), the first data access fetches/updates
            from the network. Set False to operate purely from existing cache.
    """

    def __init__(
        self,
        cache_path: Optional[os.PathLike | str] = None,
        url: str = DEFAULT_URL,
        timeout: float = 15,
        auto_refresh: bool = True,
    ) -> None:
        self.cache_path = Path(cache_path).expanduser() if cache_path else DEFAULT_CACHE_PATH
        self.url = url
        self.timeout = timeout
        self.auto_refresh = auto_refresh
        self._metadata: List[str] = list(DEFAULT_METADATA)
        self._data: Optional[Dict[str, List[str]]] = None  # None => not yet loaded

    # -- internals -----------------------------------------------------------

    def _read_cache(self) -> Dict:
        """Read the on-disk cache, tolerating both historical cache shapes.

        Returns a normalized dict ``{"metadata": [...], "data": {...}, "etag": ...}``.
        Handles the two shapes used across the constellation:
          * ``{"metadata", "data", "etag"}``  (nse-corporate-data, FirstFilingsIN, ...)
          * ``{"etag", "data"}``              (surveillance-tracker-in)
        """
        out = {"metadata": list(DEFAULT_METADATA), "data": {}, "etag": None}
        if not self.cache_path.exists():
            return out
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if isinstance(cached, dict):
                if isinstance(cached.get("metadata"), list) and cached["metadata"]:
                    out["metadata"] = cached["metadata"]
                if isinstance(cached.get("data"), dict):
                    out["data"] = cached["data"]
                out["etag"] = cached.get("etag")
        except Exception as e:  # corrupt cache must never be fatal
            logger.warning("Failed to read industry cache %s: %s", self.cache_path, e)
        return out

    def _write_cache(self, metadata: List[str], data: Dict[str, List[str]], etag: Optional[str]) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"metadata": metadata, "data": data, "etag": etag}, f, indent=2)
            os.replace(tmp, self.cache_path)  # atomic
        except Exception as e:
            logger.warning("Failed to write industry cache %s: %s", self.cache_path, e)

    # -- public API ----------------------------------------------------------

    def refresh(self) -> "IndustryMap":
        """Force a conditional fetch from the source and update the cache.

        Network/parse failures fall back to existing cache (or empty), never
        raising — matching every prior consumer's resilience contract.
        """
        cached = self._read_cache()
        headers = {}
        if cached.get("etag"):
            headers["If-None-Match"] = cached["etag"]

        logger.info("Checking for industry data updates...")
        try:
            req = urllib.request.Request(self.url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                etag = response.headers.get("ETag")
                metadata = payload.get("metadata") or list(DEFAULT_METADATA)
                data = payload.get("data", {})
                self._write_cache(metadata, data, etag)
                logger.info("Industry data updated and cached.")
                self._metadata, self._data = metadata, data
                return self
        except Exception as e:
            # urllib surfaces HTTP 304 (Not Modified) as an HTTPError.
            if isinstance(e, HTTPError) and e.code == 304:
                logger.info("Industry data is up to date (304 Not Modified).")
                self._metadata, self._data = cached["metadata"], cached["data"]
                return self
            logger.error("Failed to fetch/update industry data: %s", e)
            if cached.get("data"):
                logger.info("Falling back to local industry cache.")
                self._metadata, self._data = cached["metadata"], cached["data"]
            else:
                self._metadata, self._data = list(DEFAULT_METADATA), {}
            return self

    def _ensure_loaded(self) -> None:
        if self._data is not None:
            return
        if self.auto_refresh:
            self.refresh()
        else:  # cache-only mode
            cached = self._read_cache()
            self._metadata, self._data = cached["metadata"], cached["data"]

    @property
    def metadata(self) -> List[str]:
        """The level names, e.g. ``["Macro", "Sector", "Industry", "Basic Industry"]``."""
        self._ensure_loaded()
        return self._metadata

    @property
    def data(self) -> Dict[str, List[str]]:
        """The full ``{SYMBOL: [levels...]}`` mapping."""
        self._ensure_loaded()
        return self._data or {}

    def as_payload(self) -> Dict[str, object]:
        """Return ``{"metadata": [...], "data": {...}}`` (nse-corporate-data shape)."""
        return {"metadata": self.metadata, "data": self.data}

    def levels(self, symbol: Optional[str]) -> Optional[List[str]]:
        """Return the full level list for ``symbol`` (case-insensitive), or None."""
        if not symbol:
            return None
        d = self.data
        sym = symbol.strip().upper()
        levels = d.get(sym)
        if not levels and sym not in d:
            levels = d.get(symbol.strip())
        return levels if isinstance(levels, list) and levels else None

    # Alias kept for callers that prefer dict-like .get semantics.
    def get(self, symbol: Optional[str]) -> Optional[List[str]]:
        return self.levels(symbol)

    def industry(self, symbol: Optional[str]) -> Optional[str]:
        """Return the most-specific level (last item, e.g. 'Basic Industry'), or None."""
        levels = self.levels(symbol)
        return levels[-1] if levels else None

    def classify(self, symbol: Optional[str]) -> Optional[Dict[str, str]]:
        """Return ``{level_name: value}`` mapping for ``symbol``, or None.

        Example: ``{"Macro": "Industrials", "Sector": "Capital Goods",
        "Industry": "Electrical Equipment", "Basic Industry": "Heavy Electrical Equipment"}``.
        """
        levels = self.levels(symbol)
        if not levels:
            return None
        names = self.metadata
        return {names[i] if i < len(names) else f"level_{i}": v for i, v in enumerate(levels)}


# ---------------------------------------------------------------------------
# Module-level convenience API (memoized singleton) — drop-in for the legacy
# free functions used across the consumers.
# ---------------------------------------------------------------------------

_default_map: Optional[IndustryMap] = None


def _singleton() -> IndustryMap:
    global _default_map
    if _default_map is None:
        _default_map = IndustryMap()
    return _default_map


def get_industry_map() -> Dict[str, List[str]]:
    """Return ``{SYMBOL: [levels...]}`` (FirstFilingsIN / IndiaInc / surveillance shape)."""
    return _singleton().data


def get_industry_data() -> Dict[str, object]:
    """Return ``{"metadata": [...], "data": {...}}`` (nse-corporate-data shape)."""
    return _singleton().as_payload()


def get_company_industry(symbol: str) -> Optional[str]:
    """Return the most-specific industry level for ``symbol`` (FirstFilingsIN / IndiaInc shape)."""
    return _singleton().industry(symbol)
