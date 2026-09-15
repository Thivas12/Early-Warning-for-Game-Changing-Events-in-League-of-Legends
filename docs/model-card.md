# Model card: RiftHazard candidate

Status: **research design; not trained on an eligible v2 dataset and not
approved for player-facing use**.

## Intended use

Offline research and, only after Gate G6, post-match coaching that highlights
moments worth reviewing. A probability should support several player choices,
not dictate an action.

## Out of scope

- betting, gambling, ranking or hidden-MMR estimation;
- revealing information unavailable in the normal game client;
- automated gameplay or a live instruction engine;
- discipline, scouting or evaluation of identifiable individual players;
- use on a patch outside the model's declared support without abstention.

## Inputs and outputs

Inputs are causal observations at or before a timestamp, represented as a
patch-aware temporal graph. Outputs are calibrated cumulative risks for Baron,
Dragon and teamfight-proxy events at fixed future horizons, plus an OOD score
and abstention flag.

The discrete-hazard output parameterization must satisfy
`risk(10s) <= risk(20s) <= risk(30s) <= risk(60s)` by construction.

## Required evaluation before release

- future-patch, match-disjoint test;
- repeated seeds and whole-match bootstrap intervals;
- all registered ablations;
- calibration and reliability diagrams;
- operational warning metrics and alert-burden simulation;
- latency/memory on the target free-tier CPU;
- slice analysis and documented failure cases;
- policy, privacy and human review.

## Known risks

Schedule priors can masquerade as intelligence. Incorrect teamfight proxies can
reward predictions after combat has effectively begun. Distribution drift may
create confident false alerts. Explanations can be plausible without being
causal. Alerting can narrow decisions or distract players. These risks require
time-only controls, episode sensitivity analyses, calibration/OOD monitoring,
faithfulness tests and a post-match-first product design.
