# Threat model

## Assets

- integrity of experiment configuration and retained results;
- confidentiality of the local filesystem outside the chosen output directory;
- reproducibility of numerical evidence.

## Relevant threats

- path traversal or writing outside the requested output directory;
- accidental credential inclusion in a release;
- maliciously large configurations causing local resource exhaustion;
- silent numerical failure producing apparently valid metrics;
- future-data leakage invalidating an experiment.

## Controls

- the CLI creates only the explicit local output path;
- no network or credential surface exists;
- validation rejects underspecified or invalid configurations;
- optimizers expose convergence state and failure counts;
- leakage is covered by a future-mutation invariant;
- the release verifier performs a credential-pattern scan.

## Out of scope

RiskLab is not a multi-tenant service and does not sandbox arbitrary Python. A user who can modify the repository can execute code with that user's privileges.
