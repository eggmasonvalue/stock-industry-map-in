# MAP

## Repository layout

```text
.
├─ main.py                         # Producer CLI entrypoint
├─ src/
│  ├─ orchestrator.py              # Producer workflow coordinator
│  ├─ nse_client.py                # NSE fetch adapter via exchange-access
│  ├─ bse_client.py                # BSE fetch adapter via exchange-access
│  └─ store.py                     # JSON artifact persistence
├─ out/industry_data.json          # Produced artifact (tracked output)
├─ industry_map_client/            # Consumer package shipped to downstream repos
│  ├─ client.py                    # ETag-aware cache + lookup API
│  ├─ __main__.py                  # consumer CLI (`python -m industry_map_client`)
│  └─ __init__.py                  # exported API
├─ tests/
│  └─ test_industry_map_client.py  # Offline tests for consumer cache behavior
└─ .github/workflows/update_industry_data.yml
   # Scheduled/manual producer refresh workflow
```

## Data flow

```mermaid
flowchart TD
    A[main.py CLI\n--refresh | --full-refresh\n--frequency daily/weekly/monthly] --> B[Orchestrator]
    B --> C[Configure retry cadence\nset_retry_config on NSE/BSE adapters]
    B --> D[NSE adapter\nsrc/nse_client.py]
    B --> E[BSE adapter\nsrc/bse_client.py]
    D --> F[exchange-access NSEClient\nshared retry predicate + transport seam]
    E --> G[exchange-access BSEClient\nshared retry predicate + transport seam]
    B --> H[Store\nout/industry_data.json]
    H --> I[Published artifact in repo]
    I --> J[industry_map_client\nETag/cache consumer]
    J --> K[Downstream repos\nstdlib-only lookup API]
```

## Producer execution modes

- `--full-refresh`: clear store, fetch BSE first, then fill remaining symbols from NSE mainboard and SME.
- `--refresh`: load store and fill missing/incomplete symbols across NSE mainboard, NSE SME, and BSE.
- Retry cadence is dynamic (`daily`, `weekly`, `monthly`) and propagated into both exchange adapters.

## Consumer package boundary

- Only `industry_map_client` is packaged in the distribution (`[tool.setuptools].packages`).
- Producer code (`main.py`, `src/`) remains run-in-place for maintainers/CI and is not installed into consumer environments.
- Consumer runtime stays stdlib-only and serves symbol→industry lookups from cached/published artifact data.
