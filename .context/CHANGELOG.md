# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- **Core Functionality:** Implemented `main.py`, `src/orchestrator.py`, `src/store.py`, `src/nse_client.py`, and `src/bse_client.py`.
- **NSE Support:** Full implementation of `NSEClient` with Mainboard and SME support.
- **BSE Support:** Full implementation of `BSEClient` iterating all security groups.
- **Data Persistence:** JSON storage (`out/industry_data.json`) with load/save capabilities.
- **CLI:** `argparse` integration for `refresh`, `full-refresh`, and `frequency` options.
- **Retry Logic:** Robust `tenacity` integration with configurable backoff strategies.
- **GitHub Actions:** HTTP/2 optimization for CI environments.

### Fixed
- **CI Workflow:** Added `git pull --rebase` step to `update_industry_data.yml` to prevent non-fast-forward push errors.

### Changed
- **Data Location:** Moved `industry_data.json` to `out/` directory.

## [0.1.0] - 2026-02-21
### Added
- Initial repository structure.
- MIT License.
- `.gitignore` ignoring `clipboard.md`.
- `GEMINI.md` context rule.
- `.context/` documentation artifacts.
