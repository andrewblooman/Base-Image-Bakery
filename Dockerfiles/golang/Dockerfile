ARG GO_VERSION=1.24
FROM golang:${GO_VERSION}-alpine

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.24
ARG IMAGE_SOURCE

# Install ca-certificates and copy custom CA certificates
RUN apk add --no-cache ca-certificates git
COPY certs/ /usr/local/share/ca-certificates/custom/
RUN update-ca-certificates

# Apply latest security patches
RUN apk upgrade --no-cache

# Configure Go environment
ENV GOPATH=/go
ENV CGO_ENABLED=0
ENV GOPROXY=https://proxy.golang.org,direct
ENV GONOSUMCHECK=""

# OCI-standard image labels
LABEL org.opencontainers.image.title="Base Golang" \
      org.opencontainers.image.description="Custom Go base image with imported CA certificates and security defaults" \
      org.opencontainers.image.vendor="Base Image Bakery" \
      org.opencontainers.image.source="${IMAGE_SOURCE}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.base.name="golang:${GO_VERSION}-alpine"

# Create a non-root application user for running built binaries
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

USER appuser

CMD ["/bin/sh"]
