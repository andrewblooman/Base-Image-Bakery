# Copilot Instructions

## What This Repo Does

Base Image Bakery is a GitHub Actions CI/CD pipeline that builds, vulnerability-scans, signs, and publishes hardened Docker base images to Docker Hub. There is no application code — the primary artefacts are Dockerfiles and the workflow that processes them.

## Building Images Locally

Build from the **repo root** — the Docker context must include `certs/`:

```bash
docker build -f Dockerfiles/alpine/Dockerfile \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --build-arg ALPINE_VERSION=3.21 \
  --build-arg IMAGE_SOURCE=https://github.com/andrewblooman/Base-Image-Bakery \
  -t base-alpine:local .
```

Scan locally with Grype:

```bash
grype base-alpine:local --output json --file grype-results-alpine.json
```

Run the Claude analysis script against local scan results:

```bash
ANTHROPIC_API_KEY=<key> python3 .github/scripts/analyse-scan-results.py ./
```

## Architecture

### Pipeline Flow (`build-images.yml`)

Each image runs as a **parallel matrix job** (`fail-fast: false`):

1. Build image locally tagged `bakery/<name>:scan-target` (not pushed yet)
2. Grype vulnerability scan → JSON artefact (90-day retention)
3. Syft SBOM → SPDX JSON artefact (90-day retention)
4. Push to Docker Hub *(skipped on PRs)*
5. Cosign keyless sign via GitHub OIDC *(skipped on PRs)*
6. `cosign attest --type spdxjson` — attaches SBOM to image in Rekor *(skipped on PRs)*
7. `cosign attest --type slsaprovenance` — attaches build provenance in Rekor *(skipped on PRs)*

After all matrix jobs, a single `review-scan-results` job (runs `if: always()`) downloads every Grype artefact and calls `analyse-scan-results.py`. The Markdown security report is written to `$GITHUB_STEP_SUMMARY`. On pull requests it is also posted as a PR comment via a GitHub App token (`APP_ID` + `APP_PRIVATE_KEY`).

### `analyse-scan-results.py`

Uses only the Python standard library — no third-party packages, no Anthropic SDK. It calls `https://api.anthropic.com/v1/messages` directly with `urllib.request`. Reads `grype-results-*.json` files, caps Critical/High findings at 20 per image to keep the prompt size manageable, and calls `claude-opus-4-5` with `max_tokens=4096`. Output goes to stdout; the workflow captures it with `tee`.

## Key Conventions

### Dockerfile Structure

Every Dockerfile must follow this order and include all of these elements:

1. `ARG <NAME>_VERSION=<default>` then `FROM image:${<NAME>_VERSION}` — base image version controlled via the image-specific ARG
2. Declare `BUILD_DATE`, `VCS_REF`, `VERSION`, `IMAGE_SOURCE` build args
3. Install `ca-certificates`, then `COPY certs/ /usr/local/share/ca-certificates/custom/` and run the OS cert-update command
4. Apply security patches (`apk upgrade --no-cache` for Alpine; `apt-get upgrade -y` + cleanup for Debian)
5. OCI-standard `LABEL` block using all four build args
6. Create a non-root user (`addgroup`/`adduser` on Alpine; `groupadd`/`useradd` on Debian) and `USER appuser`

Exception: `docker-in-docker` runs as root (required by the Docker daemon).

**Eclipse Temurin extra step:** after OS cert import, also loop `.crt` files into the JVM truststore with `keytool -importcert`.

**Python extra step:** set `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `PYTHONDONTWRITEBYTECODE`, and `PYTHONUNBUFFERED` env vars.

### Adding a New Image

1. `Dockerfiles/<name>/Dockerfile` — follow the conventions above
2. Add a matrix entry to `.github/workflows/build-images.yml` (fields: `name`, `dockerfile`, `repo`, `version`)
3. Update the Image Inventory table in `README.md`

### Updating a Base Image Version

1. Change `ARG <X>_VERSION=` default in the Dockerfile
2. Update `version` in the workflow matrix entry
3. Update the Image Inventory table in `README.md`

### CA Certificates

Drop PEM-format `.crt` files into `certs/`. They are baked into every image at build time. Non-`.crt` files are excluded via `.dockerignore`.

### Workflow Triggers

The pipeline runs on: push to `main` (paths: `Dockerfiles/**`, `certs/**`, workflow/script files), pull requests to `main` (same paths), every Monday at 06:00 UTC (scheduled), and `workflow_dispatch`.

## Required Secrets

| Secret | Purpose |
|--------|---------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token (Read & Write) |
| `ANTHROPIC_API_KEY` | Used by `analyse-scan-results.py` |
| `APP_ID` | GitHub App ID for security-engineer-agent |
| `APP_PRIVATE_KEY` | GitHub App private key (PEM) |
