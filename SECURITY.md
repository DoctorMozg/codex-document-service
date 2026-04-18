# Security Policy

## Reporting a vulnerability

If you discover a security issue, **please do not open a public issue**. Instead, report it privately via one of:

- Email: `drmozg@gmail.com`
- GitHub: use [private vulnerability reporting](https://github.com/DoctorMozg/codex-document-service/security/advisories/new)

Include:
- A description of the issue and potential impact
- Steps to reproduce (or a minimal PoC)
- Affected version / commit hash

You can expect an acknowledgement within a few days.

## Supported versions

This project is in active development; only the `main` branch is supported.

## Scope

In-scope: the `drm_document_service` package, the CLI, and the default `docker-compose` configuration.

Out-of-scope:
- Third-party services (OpenAI, Qdrant, MinIO) — report to the respective vendors
- The default MinIO credentials in `doc-service.compose.yaml` are **demo-only**; do not use them in production
