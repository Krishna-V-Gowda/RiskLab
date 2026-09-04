# Failure log

## 1. Optimizing at every observation

**Failure.** An early prototype solved every constrained allocation on every day. Runtime grew rapidly, but the additional solves did not correspond to an economically meaningful policy.

**Change.** Decisions now occur only at a declared rebalance interval. Weights drift between decisions, which also makes turnover accounting meaningful.

**Lesson.** More computation is not more rigor; the execution policy must precede optimization.

## 2. Treating optimizer fallback as success

**Failure.** Returning equal weight after a failed solve made downstream reports look complete while erasing a material numerical result.

**Change.** A failed solve retains the previous feasible portfolio and increments an explicit per-method failure count.

**Lesson.** Failure containment and failure disclosure are different requirements; both are necessary.

## 3. Ambiguous drawdown origin

**Failure.** A first metric implementation started its peak sequence after the first return, which can understate a first-period loss.

**Change.** Wealth now begins at 1.0 before any observation, and a regression test fixes the definition.

**Lesson.** Even familiar metrics require a written convention and an edge-case test.
