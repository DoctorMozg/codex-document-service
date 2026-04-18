# Contributing

Thanks for your interest in contributing! This project is a personal portfolio piece, but PRs and issues are welcome.

## Development setup

```bash
uv sync
cp .env.example .env  # add your OPEN_AI_KEY
uv run pre-commit install
```

## Running checks

```bash
uv run ruff check .           # lint
uv run ruff format .          # format
uv run mypy --config-file mypy.ini drm_document_service
uv run pytest                 # requires Docker (testcontainers)
```

Pre-commit runs lint, format, and mypy automatically on staged files.

## Pull requests

- Keep PRs focused — one concern per PR.
- Make sure `ruff`, `mypy`, and `pytest` pass locally before opening.
- Update `README.md` if you change public-facing behavior (API, CLI, config).
- New endpoints get a docstring (it becomes the OpenAPI description).

## Commit style

Short imperative subjects, optionally prefixed with a type (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`). One logical change per commit.

## Reporting bugs or requesting features

Use the issue templates in `.github/ISSUE_TEMPLATE/`. For security issues, see [SECURITY.md](SECURITY.md) instead.
