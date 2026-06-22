# Architecture

This project is built as a command-line application (CLI) using Python. It orchestrates data fetching from NSE and BSE and persists the results in a local JSON store.

## Components

### 1. `main.py`
- **Purpose:** Entry point for the application.
- **Responsibilities:**
  - Parses command-line arguments (`--refresh`, `--full-refresh`, `--frequency`).
  - Initializes the `Orchestrator` with the selected frequency configuration.
  - Triggers the appropriate workflow (refresh or full refresh).

### 2. `src.orchestrator.Orchestrator`
- **Purpose:** Controls the high-level workflow of data fetching and updates.
- **Responsibilities:**
  - Manages the `Store` and API clients (`NSEClient`, `BSEClient`).
  - Coordinates the sequence of operations:
    - `full_refresh`: Clears store, fetches BSE, then fills gaps with NSE data.
    - `refresh`: Updates missing entries for NSE Mainboard, NSE SME, and BSE sequentially.
  - Implements batch saving (every 50 records) to minimize data loss.
  - Configures retry policies based on execution frequency (daily, weekly, monthly).

### 3. `src.store.Store`
- **Purpose:** Handles data persistence.
- **Responsibilities:**
  - Loads and saves data to `out/industry_data.json`.
  - Maintains the data structure:
    ```json
    {
      "metadata": ["Macro", "Sector", "Industry", "Basic Industry"],
      "data": {
        "SYMBOL": ["Macro Value", "Sector Value", "Industry Value", "Basic Industry Value"]
      }
    }
    ```
  - Provides methods for updating and retrieving stock information.

### 4. `src.nse_client.NSEClient`
- **Purpose:** Interacts with the National Stock Exchange (NSE) API.
- **Responsibilities:**
  - Wraps the `NseIndiaApi` library.
  - Fetches Mainboard and SME symbol lists (CSV).
  - Fetches detailed industry information (`fetch_symbol_data`).
  - Handles SME-specific logic (trying 'SM' then 'ST' series).
  - Implements robust retry logic using `tenacity` (handling 404s appropriately).
  - Optimizes for GitHub Actions environments (using HTTP/2 via `httpx`).

### 5. `src.bse_client.BseClient`
- **Purpose:** Interacts with the Bombay Stock Exchange (BSE) API.
- **Responsibilities:**
  - Wraps the `BseIndiaApi` library.
  - Iterates through all security groups (A, B, etc.) to fetch a complete list of securities.
  - Fetches industry metadata (`equityMetaInfo`).
  - Maps BSE fields to the standardized industry schema (Sector -> Macro, IndustryNew -> Sector, etc.).
  - Implements retry logic for network resilience.

## Data Flow

### 6. `industry_map_client` (consumer client package)
- **Purpose:** The *consumer* half of this repo — lets sibling apps read the
  published `out/industry_data.json` without re-implementing the fetch/cache.
- **Responsibilities:**
  - Conditional (ETag/`If-None-Match`) download of the GitHub-raw artifact.
  - Local cache (`~/.industry_map_in/industry_cache.json` by default; path is
    configurable) with fallback-to-cache on any network/parse error.
  - Tolerates both historical on-disk cache shapes (`{metadata,data,etag}` and
    `{etag,data}`).
  - Exposes the union of every prior consumer's return shape:
    `get_industry_data()` -> `{metadata,data}`; `get_industry_map()` ->
    `{SYMBOL:[levels]}`; `get_company_industry(symbol)` -> last level; plus an
    `IndustryMap` class (`levels`/`industry`/`classify`/`as_payload`).
- **Dependencies:** **stdlib only** (deliberately no nse/bse/tenacity/httpx).
- **Packaging:** `pyproject` ships only `industry_map_client`; the producer
  (`main.py`, `src/`) stays a run-in-place script set and is not installed.

1.  **Initialization:** `main.py` instantiates `Orchestrator`, which loads `Store` and initializes `NSEClient` and `BSEClient`.
2.  **Fetching (e.g., Full Refresh):**
    - `Orchestrator` requests BSE securities list from `BSEClient`.
    - Iterates through BSE securities, fetching industry info via `BSEClient`.
    - Updates `Store` with BSE data.
    - `Orchestrator` requests NSE Mainboard symbols from `NSEClient`.
    - Filters for symbols *not* already in `Store` (BSE data takes precedence in this flow).
    - Fetches missing NSE info via `NSEClient`.
    - Repeats for NSE SME symbols.
3.  **Persistence:** `Store` saves the `data` dictionary to `out/industry_data.json` periodically and upon completion.

## External Dependencies

- **`NseIndiaApi`**: Unofficial NSE API wrapper.
- **`BseIndiaApi`**: Unofficial BSE API wrapper.
- **`tenacity`**: Retry library for handling transient network errors.
- **`httpx`**: Modern HTTP client for efficient requests (HTTP/2 support).
