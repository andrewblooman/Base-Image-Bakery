ARG ALPINE_VERSION=3.21
FROM alpine:${ALPINE_VERSION}

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=3.21
ARG IMAGE_SOURCE

# Install ca-certificates package first so update-ca-certificates is available
RUN apk add --no-cache ca-certificates

# Copy custom CA certificates (place .crt files in the repo's certs/ directory)
COPY certs/ /usr/local/share/ca-certificates/custom/
RUN update-ca-certificates

# Apply latest security patches
RUN apk upgrade --no-cache

# Install common utility packages
RUN apk add --no-cache \
    bash \
    curl \
    wget \
    tzdata

# OCI-standard image labels
LABEL org.opencontainers.image.title="Base Alpine" \
      org.opencontainers.image.description="Custom base Alpine image with imported CA certificates and security defaults" \
      org.opencontainers.image.vendor="Base Image Bakery" \
      org.opencontainers.image.source="${IMAGE_SOURCE}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.base.name="alpine:${ALPINE_VERSION}"

# Create a non-root application user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

USER appuser

CMD ["/bin/bash"]
