ARG GO_VERSION=1.24
FROM cgr.dev/chainguard/go:latest-dev

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.24
ARG IMAGE_SOURCE

USER root

# Install ca-certificates and git; import custom certs from the repo's certs/ directory
RUN apk add --no-cache ca-certificates git
COPY certs/ /usr/local/share/ca-certificates/custom/
RUN update-ca-certificates

# Configure Go environment
ENV GOPATH=/go
ENV CGO_ENABLED=0
ENV GOPROXY=https://proxy.golang.org,direct
ENV GONOSUMCHECK=""

# OCI-standard image labels
LABEL org.opencontainers.image.title="Base Golang" \
      org.opencontainers.image.description="Custom Go base image (Chainguard/Wolfi) with imported CA certificates and security defaults" \
      org.opencontainers.image.vendor="Base Image Bakery" \
      org.opencontainers.image.source="${IMAGE_SOURCE}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.base.name="cgr.dev/chainguard/go:latest-dev"

USER nonroot

CMD ["/bin/sh"]
