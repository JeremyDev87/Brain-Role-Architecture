# Security policy

## Release status

<!-- release-state: source=PRE_RELEASE github=v0.4.0:prerelease registry=unpublished deployment=none -->

`0.4.0` remains a PRE_RELEASE source candidate. Its annotated tag and GitHub Pre-release provide downloadable
artifacts, but they do not represent stable support, registry availability, a deployment, or a production-safety guarantee.

## Reporting

Please use GitHub private vulnerability reporting when available. Do not include credentials, personal
canon, real session/state data, or production private overlays in reports or fixtures.

## Security boundary

The reference validator, compiler, and simulator are offline and do not activate runtimes. File-based checks
do not prove repository settings, branch protection, environment approvals, or external service safety.
Validation does not grant publication authority.
