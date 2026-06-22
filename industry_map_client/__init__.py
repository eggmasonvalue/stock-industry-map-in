"""Consumer client for the stock-industry-map-in published artifact.

This is the single shared client that replaces the ~30-line ETag-cached
fetcher copy-pasted across the constellation (nse-corporate-data,
FirstFilingsIN, IndiaInc-today, knowledgelm-nse, surveillance-tracker-in).

It is the *consumer* half of this repo: the producer (``main.py`` /
``src/orchestrator.py``) builds and publishes ``out/industry_data.json``; this
package fetches that published artifact with conditional (ETag) requests and a
local cache, then exposes it as a lookup.

Design goals:
- **Zero runtime dependencies** (stdlib ``urllib`` only) so any app can install
  it without dragging in httpx/tenacity.
- **Union of every existing consumer's return shape**, so each migration is a
  drop-in:
    * ``get_industry_data()``  -> ``{"metadata": [...], "data": {...}}``  (nse-corporate-data)
    * ``get_industry_map()``   -> ``{SYMBOL: [levels...]}``               (FirstFilingsIN, IndiaInc-today, surveillance)
    * ``get_company_industry(symbol)`` -> last level string               (FirstFilingsIN, IndiaInc-today)
    * ``IndustryMap`` class for explicit cache-path / lifecycle control.

Quickstart::

    from industry_map_client import get_company_industry
    get_company_industry("ABB")  # -> "Heavy Electrical Equipment"

    from industry_map_client import IndustryMap
    im = IndustryMap(cache_path="~/.myapp/industry_cache.json")
    im.classify("ABB")  # -> {"Macro": "Industrials", ..., "Basic Industry": "Heavy Electrical Equipment"}
"""

from .client import (
    DEFAULT_CACHE_PATH,
    DEFAULT_URL,
    IndustryMap,
    get_company_industry,
    get_industry_data,
    get_industry_map,
)

__all__ = [
    "IndustryMap",
    "get_industry_map",
    "get_company_industry",
    "get_industry_data",
    "DEFAULT_URL",
    "DEFAULT_CACHE_PATH",
]

__version__ = "0.1.0"
