ARG JAVA_VERSION=21
FROM cgr.dev/chainguard/jre:latest-dev

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=21
ARG IMAGE_SOURCE

USER root

# Install ca-certificates and import custom certs from the repo's certs/ directory
RUN apk add --no-cache ca-certificates
COPY certs/ /usr/local/share/ca-certificates/custom/
RUN update-ca-certificates

# Import custom certs into the JVM truststore (no-op when certs/ is empty)
RUN find /usr/local/share/ca-certificates/custom -name "*.crt" -type f \
    | while read -r cert; do \
        alias_name="custom-$(basename "$cert" .crt)"; \
        keytool -importcert -noprompt -trustcacerts \
            -alias "$alias_name" \
            -file "$cert" \
            -keystore "$JAVA_HOME/lib/security/cacerts" \
            -storepass changeit; \
    done

# OCI-standard image labels
LABEL org.opencontainers.image.title="Base JRE" \
      org.opencontainers.image.description="Custom JRE base image (Chainguard/Wolfi) with imported CA certificates and security defaults" \
      org.opencontainers.image.vendor="Base Image Bakery" \
      org.opencontainers.image.source="${IMAGE_SOURCE}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.base.name="cgr.dev/chainguard/jre:latest-dev"

USER nonroot

CMD ["/bin/bash"]
