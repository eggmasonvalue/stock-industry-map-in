# DECISIONS

## 2026-06-22 — Split producer pipeline and consumer client in one repo

Context: Multiple sibling repositories needed the same industry lookup behavior and had copy-pasted fetch/cache code.
Decision: Keep both concerns in this repository: (1) producer pipeline (`main.py`, `src/`) that builds `out/industry_data.json`, and (2) installable `industry_map_client` that consumes the published artifact.
Tradeoff: The repo now has two execution surfaces and more boundary discipline is required, but shared logic and drift across consumers are reduced.
Status: active

## 2026-06-22 — Keep consumer install path zero-dependency

Context: Downstream projects should be able to install `industry-data-in` just for `industry_map_client` without pulling exchange/network stack dependencies.
Decision: Keep `[project].dependencies = []` and place producer runtime dependencies only in PEP 735 group `producer` (installed via `uv` default groups for maintainers/CI).
Tradeoff: Packaging model is less typical and requires care not to move producer deps into project dependencies.
Status: active

## 2026-06-22 — Use shared `exchange-access` and remove local retry/transport duplication

Context: This producer previously carried local exchange wrapper/retry behavior that also existed in sibling repos.
Decision: Consume `exchange-access` as the shared L1 dependency and wire retries through `RetryProfile` + `build_retry` in both NSE/BSE adapters.
Tradeoff: Adds coupling to shared library release management, but centralizes transport/retry policy and eliminates duplicated local implementations.
Status: active

## 2026-06-22 — Keep dynamic retry cadence per run frequency

Context: Daily runs should fail fast, while weekly/monthly maintenance runs can tolerate longer backoff windows for exchange instability.
Decision: Orchestrator maps `daily|weekly|monthly` into max-attempt/max-wait values and passes them to both exchange adapters, which build retry decorators from shared `exchange-access` primitives.
Tradeoff: More runtime configuration paths to maintain, but better operational fit across scheduled cadences.
Status: active

## 2026-06-22 — BSE-first precedence in full refresh

Context: Full refresh needs deterministic precedence when both exchanges can supply overlapping symbols.
Decision: In `full_refresh`, process BSE first and only fetch NSE for symbols still missing/incomplete.
Tradeoff: NSE-specific metadata for dual-listed symbols may be ignored in that mode.
Status: active
