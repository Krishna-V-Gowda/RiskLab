# Contributing

1. Create a focused branch.
2. Preserve temporal integrity: an allocation at `t` may not observe `returns[t:]`.
3. Add a deterministic test for every numerical or state transition change.
4. Run `bash scripts/verify.sh`.
5. State whether an observed change is mathematical, numerical, or merely presentational.

New allocation methods must document their objective, constraints, failure conditions, and comparison baseline. New empirical claims require a retained machine-readable result and an explicit limitation.
