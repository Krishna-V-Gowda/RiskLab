# Data provenance

The release distributes **no historical or proprietary market data**.

The complete input is generated locally by `risklab.simulate.simulate_market` from:

- NumPy's PCG64-backed default generator;
- the seed retained in `results.json`;
- explicit regime parameters in source;
- deterministic factor loadings and Student-t draws;
- an explicit clipping boundary.

`results.json` contains a SHA-256 digest of the little-endian float64 return matrix. This permits exact-path identity checks without distributing a separate opaque dataset. The synthetic process is licensed as part of this MIT repository.
