"""CLI: refresh the local industry-data cache and emit JSON status to stdout.

Replaces ``knowledgelm-nse/scripts/fetch_industry_data.py``. Logs go to stderr
(house style: JSON to stdout, logs to file/stderr).

Usage::

    python -m industry_map_client                 # refresh default cache
    python -m industry_map_client --cache PATH     # refresh a specific cache file
    python -m industry_map_client --no-refresh     # report cache status only
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from .client import DEFAULT_CACHE_PATH, IndustryMap


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="industry_map_client",
        description="Refresh the published stock-industry-map-in cache (JSON status to stdout).",
    )
    parser.add_argument(
        "--cache",
        default=str(DEFAULT_CACHE_PATH),
        help=f"Cache file path (default: {DEFAULT_CACHE_PATH}).",
    )
    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="Do not hit the network; report status from existing cache only.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logs to stderr.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    im = IndustryMap(cache_path=args.cache, auto_refresh=not args.no_refresh)
    try:
        if not args.no_refresh:
            im.refresh()
        count = len(im.data)
    except Exception as e:  # should be unreachable (refresh is non-raising) but be safe
        print(json.dumps({"success": False, "error": str(e)}))
        return 1

    if count == 0 and not im.cache_path.exists():
        print(json.dumps({"success": False, "error": "no data fetched and no cache exists"}))
        return 1

    print(
        json.dumps(
            {
                "success": True,
                "cache_path": str(im.cache_path.absolute()),
                "symbols": count,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
