# industry-data-in

Four-level industry classification data for Indian public stocks (NSE + BSE), plus a zero-dependency consumer client.

## What this repo contains

- **Producer pipeline** (`main.py`, `src/`): builds/refreshes `out/industry_data.json`.
- **Consumer package** (`industry_map_client/`): stdlib-only API + CLI that fetches and caches the published artifact.

The package name is **`industry-data-in`**. It intentionally installs only `industry_map_client` so downstream consumers stay dependency-light.

## Consumer install and usage

Install directly from git:

```bash
pip install "industry-data-in @ git+https://github.com/eggmasonvalue/stock-industry-map-in.git"
```

Use in Python:

```python
from industry_map_client import get_company_industry, get_industry_map, IndustryMap

get_company_industry("ABB")
get_industry_map()["ABB"]

im = IndustryMap()
im.classify("ABB")
im.industry("ABB")
```

Refresh cache from CLI:

```bash
python -m industry_map_client
# or: industry-map-refresh
```

## Producer development

Producer dependencies are not in `[project].dependencies`; they live in PEP 735 group `producer` so consumer installs remain zero-dependency.

```bash
uv sync
```

Run incremental refresh:

```bash
uv run python main.py --refresh --frequency weekly
```

Run full rebuild:

```bash
uv run python main.py --full-refresh --frequency weekly
```

`--frequency` supports `daily`, `weekly`, `monthly` and controls retry tuning in NSE/BSE fetch adapters.

## Output shape

`out/industry_data.json`:

```json
{
  "metadata": ["Macro", "Sector", "Industry", "Basic Industry"],
  "data": {
    "SYMBOL": ["Macro", "Sector", "Industry", "Basic Industry"]
  }
}
```
