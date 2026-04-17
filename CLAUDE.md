# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Does

Base Image Bakery is a CI/CD pipeline (GitHub Actions) that builds, vulnerability-scans, signs, and publishes hardened Docker base images to Docker Hub. There is no application code to run locally — the primary artefacts are Dockerfiles and the workflow that processes them.

## Building Images Locally

```bash
# Build a single image (from repo root — context must include certs/)
docker build -f Dockerfiles/alpine/Dockerfile \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --build-arg VERSION=3.21 \
  --build-arg IMAGE_SOURCE=https://github.com/andrewblooman/Base-Image-Bakery \
  -t base-alpine:local .

# Scan locally with Grype
grype base-alpine:local --output json --file grype-results-alpine.json

# Run the Claude analysis script against local scan results
ANTHROPIC_API_KEY=<key> python3.14 .github/scripts/analyse-scan-results.py ./
```

## Architecture

### Pipeline flow (`build-images.yml`)

Each image runs as a **parallel matrix job**:
1. Build image locally (not pushed) tagged `bakery/<name>:scan-target`
2. Grype scan → JSON artefact (90-day retention)
3. Syft SBOM → SPDX JSON artefact (90-day retention)
4. Push to Docker Hub (skipped on PRs)
5. Cosign keyless sign via GitHub OIDC (skipped on PRs)
6. `cosign attest --type spdxjson` — attaches SBOM to image in Rekor (skipped on PRs)
7. `cosign attest --type slsaprovenance` — attaches build provenance to image in Rekor (skipped on PRs)

After all matrix jobs, a single `review-scan-results` job downloads all Grype artefacts and calls `analyse-scan-results.py`, which POSTs to the Anthropic API and writes a Markdown security report to `$GITHUB_STEP_SUMMARY`. On pull requests the report is also posted as a PR comment via `gh pr comment`, authenticated with a GitHub App token generated from `APP_ID` + `APP_PRIVATE_KEY` (security-engineer-agent).

### Dockerfile conventions

Every Dockerfile must:
- Accept `BUILD_DATE`, `VCS_REF`, `VERSION`, and `IMAGE_SOURCE` build args
- `COPY certs/ /usr/local/share/ca-certificates/custom/` then run the OS cert-update command
- Apply security patches (`apk upgrade --no-cache` or `apt-get upgrade -y`)
- Set OCI-standard `LABEL` instructions
- Create and switch to a non-root user (exception: docker-in-docker requires root)

### Adding a new image

1. Create `Dockerfiles/<name>/Dockerfile` following the conventions above
2. Add a matrix entry to `.github/workflows/build-images.yml` under `jobs.build-and-push.strategy.matrix.image`
3. Update the Image Inventory table in `README.md`

### CA certificates

Drop PEM-format `.crt` files into `certs/`. They are baked into every image at build time. Non-`.crt` files are excluded via `.dockerignore`.

### Updating a base image version

1. Change the `ARG <X>_VERSION=` default in the Dockerfile
2. Update the `version` field in the workflow matrix entry
3. Update the Image Inventory table in `README.md`

## Required Secrets

| Secret | Purpose |
|--------|---------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token (Read & Write) |
| `ANTHROPIC_API_KEY` | Used by `analyse-scan-results.py` to call Claude |
| `APP_ID` | GitHub App ID for security-engineer-agent (posts PR comments) |
| `APP_PRIVATE_KEY` | GitHub App private key (PEM) for security-engineer-agent |

## Python Script (`analyse-scan-results.py`)

Uses only the Python standard library plus the Anthropic REST API (raw `urllib.request` — no SDK). Reads `grype-results-*.json` files from a directory, builds a summarised prompt (capping Critical/High findings at 20 per image), and calls `claude-opus-4-5` with `max_tokens=4096`. Output goes to stdout; the workflow captures it with `tee` to both `$GITHUB_STEP_SUMMARY` and `/tmp/claude-summary.md` (used for the PR comment).
