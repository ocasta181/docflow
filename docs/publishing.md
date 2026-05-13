# Publishing Runbook

This project should publish from a clean, reviewed commit on `main`.
Local builds are useful for validation, but release artifacts should come from
GitHub Actions so the published files are reproducible from the tagged source.

## Current Release Path

The current `.github/workflows/release.yml` workflow builds the source
distribution and wheel, smoke-tests the wheel, and creates a GitHub release
when a `v*` tag is pushed.

Use this flow for a GitHub release:

```bash
git status --short
just check
```

Then update release metadata:

1. Move the next version from `CHANGELOG.md`'s `Unreleased` section into a
   dated release section.
2. Update `version` in `pyproject.toml`.
3. Run `just check` again.
4. Commit the release metadata.
5. Create and push the release tag:

```bash
git tag v0.1.1
git push origin main
git push origin v0.1.1
```

The tag push should create the GitHub release and attach the built artifacts.

## PyPI Publication

The repository should not store a PyPI token. If PyPI publication is added, use
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) with a
dedicated GitHub Actions environment instead of a long-lived `PYPI_TOKEN`
secret.

Expected PyPI publisher configuration:

- PyPI project: `docflow-cli`
- Owner/repository: `ocasta181/docflow`
- Workflow: `.github/workflows/release.yml`
- Environment: `pypi`

If PyPI upload is added to the release workflow, use
[`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish)
with job-level `id-token: write` permission and no username/password fields.
PyPI's documentation describes this as the stable public interface for trusted
publishing through GitHub Actions.

## Secrets

The project should not require repository secrets for the current GitHub release
workflow. It uses the built-in `GITHUB_TOKEN` to create releases.

Do not commit or configure these as repository secrets unless the release design
changes:

- PyPI API tokens
- TestPyPI API tokens
- GitHub personal access tokens
- local Tesseract paths or credentials

Tesseract is an external executable dependency, not a secret.

## Before Publishing

Before pushing a release tag, verify:

- `git status --short` is clean.
- `just check` passes.
- `CHANGELOG.md` has the intended release notes.
- `pyproject.toml` has the intended release version.
- `docs/cli.md` is up to date.
- The release tag matches the package version.
- No local files outside source control are needed to build the package.
