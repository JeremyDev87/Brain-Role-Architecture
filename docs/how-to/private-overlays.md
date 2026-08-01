# How to keep private overlays private

Keep personal canon, real user profiles, sessions, runtime state, credentials, private URLs, and private
operational evidence outside this repository. Public manifests may use a reference such as
`secretRef: env://SERVICE_TOKEN`; they never contain the secret value. Run `make boundary-check` before
packaging. A green scan is bounded file-based evidence, not proof about external stores or Git history.
