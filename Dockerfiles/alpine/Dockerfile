ARG ALPINE_VERSION=3.21
FROM cgr.dev/chainguard/wolfi-base

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=3.21
ARG IMAGE_SOURCE

# Install common utilities and CA certificates; import custom certs from the repo's certs/ directory
RUN apk add --no-cache \
    ca-certificates \
    bash \
    curl \
    wget \
    tzdata

COPY certs/ /usr/local/share/ca-certificates/custom/
RUN update-ca-certificates

# OCI-standard image labels
LABEL org.opencontainers.image.title="Base Wolfi" \
      org.opencontainers.image.description="Custom base image (Chainguard/Wolfi) with imported CA certificates and security defaults" \
      org.opencontainers.image.vendor="Base Image Bakery" \
      org.opencontainers.image.source="${IMAGE_SOURCE}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.base.name="cgr.dev/chainguard/wolfi-base"

# Create a non-root application user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

USER appuser

CMD ["/bin/bash"]
