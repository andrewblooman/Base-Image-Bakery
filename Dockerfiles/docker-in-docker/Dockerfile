ARG DOCKER_VERSION=27

# docker-dind has no apk; use wolfi-base to build the cert bundle then copy it in
FROM cgr.dev/chainguard/wolfi-base AS cert-builder
RUN apk add --no-cache ca-certificates
COPY certs/ /usr/local/share/ca-certificates/custom/
RUN update-ca-certificates

FROM cgr.dev/chainguard/docker-dind:latest

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=27
ARG IMAGE_SOURCE

COPY --from=cert-builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt

# OCI-standard image labels
LABEL org.opencontainers.image.title="Base Docker-in-Docker" \
      org.opencontainers.image.description="Custom Docker-in-Docker base image (Chainguard/Wolfi) with imported CA certificates and security defaults" \
      org.opencontainers.image.vendor="Base Image Bakery" \
      org.opencontainers.image.source="${IMAGE_SOURCE}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.base.name="cgr.dev/chainguard/docker-dind:latest"

# Docker daemon requires root; no user switch here
CMD ["dockerd-entrypoint.sh"]
