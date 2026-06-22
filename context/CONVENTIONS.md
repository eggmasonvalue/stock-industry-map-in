# CONVENTIONS

- Work on a branch; open a PR into `main`; never commit directly to `main`.
- Keep `[project].dependencies` empty.
- Declare producer-only runtime dependencies under `[dependency-groups].producer`.
- Pin git-based shared-library dependencies to release tags in `[tool.uv.sources]`.
- Run `uv lock` after dependency source changes.
- Run `uv sync` before executing producer commands or checks.
- Run producer refresh with `uv run python main.py --refresh --frequency <daily|weekly|monthly>`.
- Run producer full rebuild with `uv run python main.py --full-refresh --frequency <daily|weekly|monthly>`.
- Keep `industry_map_client` stdlib-only.
- Keep distribution packaging scope to `industry_map_client` via `[tool.setuptools].packages`.
- Run Python lint checks with `uv run ruff check .`.
- Run tests with `uv run pytest -q`.
- Run Markdown lint with `npx --yes markdownlint-cli2 "AGENTS.md" "README.md" "context/**/*.md"`.
- Update `context/MAP.md` when file layout or data flow changes.
- Append `context/DECISIONS.md` when an intentional tradeoff is made or reversed.
- Update `README.md` when install/usage/CLI behavior changes.
