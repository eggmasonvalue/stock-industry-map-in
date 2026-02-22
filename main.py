import argparse
import sys
from src.orchestrator import Orchestrator

def main():
    parser = argparse.ArgumentParser(description="Map stocks to their respective industry.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--refresh', action='store_true', help='Refresh missing/incomplete data.')
    group.add_argument('--full-refresh', action='store_true', help='Rebuild database from scratch.')

    args = parser.parse_args()

    orchestrator = Orchestrator()

    if args.full_refresh:
        orchestrator.full_refresh()
    elif args.refresh:
        orchestrator.refresh()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
