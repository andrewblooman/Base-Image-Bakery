# Custom CA Certificates

Place your organisation's custom CA certificate files in this directory. They will be
automatically imported and trusted in every base image built by this bakery.

## Adding Certificates

1. Export your CA certificate(s) in **PEM format** with a **`.crt`** file extension.
2. Copy the `.crt` file(s) into this `certs/` directory.
3. Commit and push to `main` to trigger a new pipeline run that bakes in the updated certs.

## Notes

- Files must use the `.crt` extension (e.g. `my-corp-root-ca.crt`).
- Multiple certificate files are supported.
- Debian/Ubuntu images: certificates are added to `/etc/ssl/certs/ca-certificates.crt`.
- Alpine images: certificates are added via `update-ca-certificates`.
- Eclipse Temurin images: certificates are also imported into the JVM truststore (`cacerts`).
- Python images: the `REQUESTS_CA_BUNDLE` and `SSL_CERT_FILE` environment variables are set
  to the system bundle so that `requests` and the standard `ssl` module pick them up automatically.
- Non-certificate files (`.md`, `.gitkeep`, etc.) are excluded from Docker build contexts via
  `.dockerignore` and will not appear inside built images.
