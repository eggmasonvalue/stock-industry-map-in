# The most comprehensive four-level industry data for Indian public stocks

- 5500+ stocks covering every active stock listed on NSE and BSE (mainboard and SME)
- Four level industry data: from macro -> sector -> industry -> basic industry
- Fields-values matrix structure for bandwidth and token savings
- Github actions refreshes it every week
- Full-refresh available via Github actions to account for any drastic changes from the exchanges
- Robust retry mechanism and update methods ensures reliability

## Consuming the data

This repo has two halves:

- **Producer** (`main.py`, `src/`): builds and publishes `out/industry_data.json`.
- **Consumer client** (`industry_map_client/`): a tiny, **zero-dependency**
  (stdlib-only) package that fetches the published artifact with conditional
  (ETag) requests + a local cache, and exposes it as a lookup. It replaces the
  ~30-line fetcher that had been copy-pasted across sibling repos.

### Install (consumers)

```bash
pip install "industry-data-in @ git+https://github.com/eggmasonvalue/stock-industry-map-in.git"
```

Installing pulls **only** `industry_map_client` (no NSE/BSE/tenacity/httpx deps).

### Use

```python
from industry_map_client import get_company_industry, get_industry_map, IndustryMap

get_company_industry("ABB")        # -> "Heavy Electrical Equipment"
get_industry_map()["ABB"]          # -> ["Industrials", "Capital Goods", "Electrical Equipment", "Heavy Electrical Equipment"]

im = IndustryMap()                  # or IndustryMap(cache_path="~/.myapp/industry_cache.json")
im.classify("ABB")                  # -> {"Macro": "Industrials", ..., "Basic Industry": "Heavy Electrical Equipment"}
im.industry("ABB")                  # -> "Heavy Electrical Equipment"
```

Refresh the cache from the CLI (JSON status to stdout):

```bash
python -m industry_map_client          # or: industry-map-refresh
```



