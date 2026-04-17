---
name: container-security-architect
description: Guides secure container base image selection, evaluation, and creation using the Chainguard ecosystem. Use this skill whenever the user is choosing a base image, migrating from Docker Hub images to Chainguard equivalents, building custom base images with apko or melange, selecting FIPS-compliant images, debugging distroless containers, or asking about Wolfi, zero-CVE image strategies, or Chainguard image variants. This skill should also trigger when the user mentions "base image", "distroless", "Chainguard", "Wolfi", "apko", "melange", or is asking which base image to use for a given stack (Python, Node, Go, Java, etc.). It complements the container-security-architect agent — use this skill first to select the right base, then let the agent handle Dockerfile authoring and supply chain operations.
---

# Secure Container Base Image Skill

This skill covers **base image selection and management** within the Chainguard ecosystem. The `container-security-architect` agent handles the broader workflow (Dockerfile authoring, scanning, signing, SBOM). This skill fills the upstream gap: choosing the right foundation before any of that begins.

## Chainguard Image Ecosystem

### Core Building Blocks

**Wolfi** is Chainguard's container-optimized Linux undistro. It uses glibc (unlike Alpine's musl), which means most compiled binaries work without recompilation. It has no kernel, no init system, and ships only what's declared.

**apko** builds OCI images declaratively from a YAML spec — no Dockerfile, no layers from shell commands. Every build is reproducible.

**melange** builds APK packages for Wolfi. Use it when your application needs a dependency that isn't in the Wolfi package repository.

**chainctl** is the Chainguard CLI for managing images, access, policies, and FIPS subscriptions.

### Image Registry

All public Chainguard images are at `cgr.dev/chainguard/<image>`. Enterprise/FIPS images use `cgr.dev/<org>/<image>`.

### Variants: `latest` vs `latest-dev`

Every Chainguard image ships in two variants:

| Variant | What's included | When to use |
|---------|----------------|-------------|
| `latest` | Runtime only — no shell, no package manager | Production runtime stage |
| `latest-dev` | Adds shell + apk package manager | Build stage, local dev, debugging |

The standard multi-stage pattern:
- Build in `latest-dev` (install deps, compile)
- Copy artifacts to `latest` (no shell, minimal surface)

## Base Image Selection Workflow

Before recommending any Chainguard image, always verify it is available on the free tier by fetching the current image directory:

```
https://images.chainguard.dev/directory/category/free
```

Fetch this URL with the WebFetch tool and check whether the image you intend to recommend is listed. The free tier changes over time — an image that was free previously may have moved to a paid tier, and new free images may have been added. Only recommend images confirmed to be on the free tier unless the user has explicitly indicated they have a Chainguard subscription.

If the needed image is not on the free tier, either:
- Suggest the closest free alternative (e.g., `wolfi-base` with manual package installation)
- Inform the user that the image requires a Chainguard subscription and explain what that means

## Selecting the Right Base Image

Match image to application type:

**Static binaries (Go, Rust with no CGO)**
→ `cgr.dev/chainguard/static` — truly empty, no libc

**Go with CGO / dynamic linking**
→ `cgr.dev/chainguard/glibc-dynamic`

**Python applications**
→ Build: `cgr.dev/chainguard/python:latest-dev`
→ Runtime: `cgr.dev/chainguard/python:latest`

**Node.js applications**
→ Build: `cgr.dev/chainguard/node:latest-dev`
→ Runtime: `cgr.dev/chainguard/node:latest`

**Java applications**
→ Build: `cgr.dev/chainguard/jdk:latest`
→ Runtime: `cgr.dev/chainguard/jre:latest`

**Applications that need a shell or apk at runtime**
→ `cgr.dev/chainguard/wolfi-base` (includes bash + apk)

**Databases / middleware**
→ `cgr.dev/chainguard/postgres`, `cgr.dev/chainguard/redis`, `cgr.dev/chainguard/nginx`, etc.

**AI/ML workloads**
→ `cgr.dev/chainguard/pytorch`, `cgr.dev/chainguard/tensorflow` (check Chainguard Academy for current availability)

## Migrating from Docker Hub Images

When migrating a `FROM python:3.11`, `FROM node:20`, `FROM ubuntu:22.04`, etc.:

1. Identify the equivalent at `cgr.dev/chainguard/<image>`
2. Switch build stage to the `latest-dev` variant
3. Move all package installation to the build stage — the runtime stage has no package manager
4. Replace `apt-get`/`apk add` in the runtime stage with `COPY --from=build` patterns
5. Remove `CMD ["sh", "-c", "..."]` — distroless has no shell at runtime; use `CMD ["/usr/bin/myapp"]` directly
6. Test with `latest-dev` first if debugging is needed, then lock to `latest` for production

Common gotchas:
- Missing timezone data → add `tzdata` in build stage, copy `/usr/share/zoneinfo` to runtime
- Missing CA certificates → `cgr.dev/chainguard/static` includes them; others may need `ca-certificates-bundle`
- Dynamic library errors → switch from `static` to `glibc-dynamic`

## Debugging Distroless Containers

No shell means no `docker exec -it <container> bash`. Options:

- **During development**: temporarily use `latest-dev` variant
- **Docker Desktop**: `docker debug <container>` attaches a debug sidecar without modifying the image
- **Kubernetes**: `kubectl debug -it <pod> --image=cgr.dev/chainguard/wolfi-base --target=<container>`
- **Application logs**: `docker logs <container>` — works without exec for most issues

## Custom Base Images with apko

When no standard Chainguard image fits, build a minimal custom image:

```yaml
# image.yaml
contents:
  repositories:
    - https://packages.wolfi.dev/os
  keyring:
    - https://packages.wolfi.dev/os/wolfi-signing.rsa.pub
  packages:
    - wolfi-baselayout
    - ca-certificates-bundle
    - python-3.12
    - py3.12-pip

accounts:
  groups:
    - groupname: nonroot
      gid: 65532
  users:
    - username: nonroot
      uid: 65532

work-dir: /app

entrypoint:
  command: /usr/bin/python3
```

Build:
```bash
apko build image.yaml myimage:latest myimage.tar
docker load < myimage.tar
```

For custom packages not in Wolfi: use melange to build an APK, then reference your local repo in `image.yaml`.

## FIPS-Compliant Images

Chainguard offers FIPS 140-2/3 validated images for regulated environments (FedRAMP, DoD, financial sector). These require an enterprise subscription. Images are at `cgr.dev/<your-org>/<image>-fips`. They use validated OpenSSL/BoringCrypto modules.

## Zero-CVE Strategy

Chainguard images target zero known CVEs at publish time. Key nuances:
- CVE counts cover OS-layer packages, not your application dependencies — scan those separately with Snyk/Trivy
- Images rebuild daily; `latest` always reflects the most current security state
- Pin by digest (`@sha256:...`) in production for reproducibility, but monitor for new CVEs in the pinned version
- `latest-dev` has more packages and thus more potential CVEs than `latest` — never ship `latest-dev` to production

## Chainguard Reference Documentation

For specific image configurations, exact package lists, chainctl usage, melange syntax, or migration guides for specific stacks, load the full Chainguard documentation bundle:

**File**: `chainguard-ai-docs.md` (in this skill's directory)

Load this when the user asks about:
- Specific image availability or package contents
- Detailed apko/melange YAML syntax
- chainctl commands
- Stack-specific migration guides (e.g., "how do I migrate my Flask app?")
- Compliance certifications and FIPS details
- CI/CD integration patterns specific to Chainguard

> Note: This file is large (~11MB). Search or read specific sections relevant to the query rather than loading the entire file.

## Handoff to container-security-architect Agent

Once a base image is selected:
1. Confirm the image name, variant, and whether digest pinning is needed
2. Hand off to the `container-security-architect` agent for:
   - Full Dockerfile authoring with security annotations
   - Vulnerability scanning of the selected base
   - SBOM generation and signing
   - CI/CD pipeline integration
