# Base Image Bakery 🍞

An automated pipeline for building, scanning, signing and publishing hardened container base
images to Docker Hub. Every image imports your organisation's CA certificates, applies
the latest security patches, and is verified with Grype (vulnerability scanning), Syft (SBOM)
and Cosign (keyless signing) before it lands in the registry.

---

## Image Inventory

| Image | Docker Hub | Base | Latest Version | Description |
|-------|-----------|------|---------------|-------------|
| Alpine | [`andyblooman/base-alpine`](https://hub.docker.com/repository/docker/andyblooman/base-alpine/general) | `alpine:3.21` | `3.21` | Lightweight Alpine Linux with common utilities and a non-root user |
| Docker-in-Docker | [`andyblooman/base-dind`](https://hub.docker.com/repository/docker/andyblooman/base-dind/general) | `docker:27-dind` | `27` | Docker daemon inside Docker — for CI pipelines that need to build images |
| Eclipse Temurin | [`andyblooman/base-eclipse-temurin`](https://hub.docker.com/repository/docker/andyblooman/base-eclipse-temurin/general) | `eclipse-temurin:21-jre-jammy` | `21` | Java 21 JRE with certs imported into both the OS and JVM truststore |
| Python | [`andyblooman/base-python`](https://hub.docker.com/repository/docker/andyblooman/base-python/general) | `python:3.13-slim-bookworm` | `3.13` | Python 3.13 slim with `REQUESTS_CA_BUNDLE` pre-configured |
| Golang | [`andyblooman/base-golang`](https://hub.docker.com/repository/docker/andyblooman/base-golang/general) | `golang:1.24-alpine` | `1.24` | Go 1.24 Alpine with static-build defaults and a non-root user |

All images include:
- ✅ Organisation CA certificates imported and trusted
- ✅ Latest upstream security patches applied at build time
- ✅ OCI-standard image labels (`org.opencontainers.image.*`)
- ✅ Non-root application user (except Docker-in-Docker, which requires root)
- ✅ Vulnerability scan report (Grype) stored as a workflow artefact
- ✅ SBOM in SPDX JSON format stored as a workflow artefact
- ✅ Cosign keyless signature verifiable via Sigstore / Rekor

---

## For Users — Consuming Images

### Pulling an image

```bash
docker pull andyblooman/base-alpine:latest
docker pull andyblooman/base-python:3.13
docker pull andyblooman/base-eclipse-temurin:21
docker pull andyblooman/base-golang:1.24
docker pull andyblooman/base-dind:27
```

### Using as a base in your own Dockerfile

```dockerfile
FROM andyblooman/base-python:3.13

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python3", "main.py"]
```

### Verifying the image signature

Every image pushed from `main` is signed using [Cosign](https://docs.sigstore.dev/cosign/overview/)
keyless signing. Verify a signature before using an image in production:

```bash
# Install Cosign (https://docs.sigstore.dev/cosign/installation/)
cosign verify \
  --certificate-identity-regexp="https://github.com/andrewblooman/Base-Image-Bakery/.github/workflows/build-images.yml" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  andyblooman/base-alpine:latest
```

Replace `base-alpine` with the image you are verifying. A successful verification prints the
Rekor transparency-log entry and confirms the image was produced by this repository's
GitHub Actions workflow.

### Checking the SBOM

SPDX JSON SBOMs are attached to every workflow run as artefacts.  
You can also generate a fresh SBOM locally:

```bash
# Install Syft (https://github.com/anchore/syft)
syft andyblooman/base-alpine:latest --output spdx-json > sbom.spdx.json
```

### Checking for vulnerabilities

```bash
# Install Grype (https://github.com/anchore/grype)
grype andyblooman/base-alpine:latest
```

---

## For Admins — Keeping Images Up to Date

### Automated rebuilds

The pipeline is triggered automatically:

| Trigger | When |
|---------|------|
| Push to `main` | Changes to `Dockerfiles/**`, `certs/**`, or the workflow itself |
| Pull request | Same paths — validates the build without pushing |
| Scheduled | Every **Monday at 06:00 UTC** — picks up upstream base-image updates |
| Manual | `workflow_dispatch` from the Actions tab |

### Adding or rotating custom CA certificates

1. Export your CA certificate in **PEM format** with a `.crt` extension.
2. Drop the file into the `certs/` directory at the root of this repository.
3. Commit and push to `main`. The pipeline will rebuild all images with the new cert.

See [`certs/README.md`](certs/README.md) for detailed guidance.

### Updating a base image version

1. Open the relevant `Dockerfiles/<image>/Dockerfile`.
2. Change the default value of the `ARG` at the top (e.g. `ARG ALPINE_VERSION=3.22`).
3. Update the `version` field in `.github/workflows/build-images.yml` under the
   corresponding matrix entry.
4. Update the Image Inventory table in this README.
5. Open a pull request. The CI will build and scan the new version before merging.

### Required repository secrets

Set the following secrets under **Settings → Secrets and variables → Actions**:

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub account username (e.g. `andyblooman`) |
| `DOCKERHUB_TOKEN` | Docker Hub [access token](https://docs.docker.com/docker-hub/access-tokens/) with **Read & Write** permissions |
| `ANTHROPIC_API_KEY` | Anthropic API key used by the Claude vulnerability-review step |

### Reviewing vulnerability scan results

After each pipeline run:

1. Open the workflow run in the **Actions** tab.
2. Select the **Review Vulnerability Scan Results with Claude** job.
3. Expand the **Analyse scan results with Claude** step to read Claude's Markdown security report.
4. Download the `grype-results-<image>` artefacts for raw Grype JSON output.
5. Download the `sbom-<image>` artefacts for SPDX SBOMs.

Artefacts are retained for **90 days**.

### Adding a new image to the bakery

1. Create a new directory under `Dockerfiles/` (e.g. `Dockerfiles/node/`).
2. Add a `Dockerfile` following the conventions of the existing images:
   - Accept `BUILD_DATE`, `VCS_REF`, `VERSION`, and `IMAGE_SOURCE` build args.
   - Copy `certs/` into the OS certificate store and run the OS cert-update command.
   - Apply `apk upgrade --no-cache` / `apt-get upgrade -y` for security patches.
   - Add OCI-standard `LABEL` instructions.
   - Create a non-root user where applicable.
3. Add a matrix entry to `.github/workflows/build-images.yml` under `jobs.build-and-push.strategy.matrix.image`.
4. Add the image to the Image Inventory table above.
5. Open a pull request for review.

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Trigger: push / PR / schedule / workflow_dispatch                  │
│                                                                     │
│  For each image (parallel matrix):                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  1. Checkout + Docker Buildx setup                           │   │
│  │  2. Build image locally (not pushed yet)                     │   │
│  │  3. Grype vulnerability scan  →  artefact (90-day retention) │   │
│  │  4. Syft SBOM generation      →  artefact (90-day retention) │   │
│  │  5. Push to Docker Hub        (skipped on PRs)               │   │
│  │  6. Cosign keyless sign       (skipped on PRs)               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  After all images:                                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  7. Download all scan results                                │   │
│  │  8. Claude (Anthropic API) analyses findings                 │   │
│  │  9. Markdown report → GitHub Step Summary                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
.
├── .github/
│   ├── scripts/
│   │   └── analyse-scan-results.py   # Claude vulnerability review script
│   └── workflows/
│       └── build-images.yml          # CI/CD pipeline
├── Dockerfiles/
│   ├── alpine/
│   │   └── Dockerfile
│   ├── docker-in-docker/
│   │   └── Dockerfile
│   ├── eclipse-temurin/
│   │   └── Dockerfile
│   ├── golang/
│   │   └── Dockerfile
│   └── python/
│       └── Dockerfile
├── certs/
│   └── README.md                     # Instructions for adding custom CA certs
├── .dockerignore
└── README.md
```

---

## License

[MIT](LICENSE)
