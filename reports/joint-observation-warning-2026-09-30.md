# Joint observation/warning experiment: rejection result

30 September 2026. **This candidate does not meet the requested breakthrough standard.**
It is retained as an isolated reproducible investigation, not promoted as the
project's scientific contribution.

## Work completed

- Exact joint acquisition/cooldown state recursion and differentiable training.
- A same-controller REINFORCE comparator with eight action samples per minibatch.
- Every phase of two-/three-tick observation schedules, plus all/none/silent controls.
- An independent known-world, full-belief Bayesian planning reference.
- 27 fits, three seeds, 2,048 training trajectories and 8,192 evaluation trajectories
  per case, across four designed synthetic cases (32,768 evaluation trajectories).
- No private League data, no final-test payloads and no GPU performance claim.

## Results

Utility is timely warnings minus wrong warnings minus .05 times acquisitions.
Higher is better. These are common prices, not matched hard-budget comparisons.
The periodic comparator below observes at the last tick before every candidate
onset, a strong clock-aligned control. The full JSON contains every method.

| Case | Exact joint | Sampled training | Periodic 3, phase 2 | Silent | Known-world planner |
|---|---:|---:|---:|---:|---:|
| Matched world | 0.1216 | 0.1195 | 0.1117 | 0.0000 | 0.1325 |
| Weaker sensor | -0.2362 | -0.2369 | -0.3398 | 0.0000 | 0.0000 |
| Higher event rate | 0.4038 | 0.4014 | 0.4917 | 0.0000 | 0.4800 |
| Uninformative sensor | -0.4828 | -0.4843 | -0.6552 | 0.0000 | 0.0000 |

On the matched case, exact joint minus the strong periodic control is
**0.00994**, with paired 95% bootstrap interval
**[-0.00157, 0.02125]**. The interval includes zero.
Under the higher event rate, that periodic control beats the proposed controller.
Under degraded sensors, silence beats the proposed controller. Small gains over
sampled gradients do not establish a substantial research advance.

Mean timed training sections: exact joint **1.675 s**, sampled
training **4.563 s**. Initialization and evaluation are excluded.
The sampled comparator uses eight action draws and the same number of optimizer
steps. This is one small CPU workload, not a general equal-compute or GPU claim.

Planner values integrate the known population law. Trained policies are evaluated
on finite new panels, so a sample estimate may exceed the population reference by
sampling variation. The planner is not allowed hidden states or future values;
it has stronger model knowledge and memory than the learned finite controller.

## Decision

Do not describe this as groundbreaking, state of the art, robust under sensor
drift, a demonstrated League improvement, or the first active-sensing algorithm.
Finite-state exact gradients, timely active sensing, and retrospective acquisition
policy evaluation have substantial prior art. The specific joint-state engineering
is sound but has not demonstrated a sufficiently consequential advance here.

No result has been omitted for being unfavorable. Periodic phase controls were
expanded after the first diagnostic; all reported comparisons are exploratory.
The simulator/cost were designed to provide nontrivial value of information.
Bootstrap intervals condition on fitted models and do not include training-data
uncertainty or multiplicity adjustment across exploratory contrasts.

## Verification

- 22 selected scientific/integration tests passed in 7.99 seconds, including six
  new tests for literal action-tree agreement, finite-difference gradients,
  causal acquisition access, deterministic cooldown boundaries, sampled-policy
  agreement, Bayesian information restrictions and generator alignment.
- Ruff lint/format passed across 212 files; whitespace checks passed.
- Report source hashes verified against the executed code. Fixed seeds are
  recorded; multithreaded floating-point kernels need not be bitwise identical.
- Existing production source and frozen private experiment modules have no edits.
  The previous full-repository result was 430 tests / 86.10% coverage; it is not
  represented as a new full-suite run for this prototype.

[Method, assumptions and primary literature](../docs/joint-observation-warning.md).
[Complete measurements and execution provenance](joint-observation-warning-2026-09-30.json).
