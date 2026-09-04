# Security policy

RiskLab is an offline numerical research tool. It does not require network access, credentials, brokerage access, or private market data.

## Supported release

Security fixes apply to the latest tagged release.

## Reporting

Open a private security advisory in the GitHub repository. Do not include credentials, non-public data, or exploit material in a public issue.

## Threat boundary

The CLI writes only below the user-selected output directory. Paths are created locally; existing result files at that location can be replaced. Input configuration is bounded and validated, but the package is not intended as a hostile multi-tenant service. Generated JSON never executes code. The verification script scans tracked text for common credential patterns.
