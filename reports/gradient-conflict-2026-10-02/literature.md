# Established method, limited mechanism claim

The primary PCGrad paper's method section and Algorithm 1 were checked on
2 October 2026. PCGrad projects each conflicting task gradient against the
original gradients of other tasks in random order, then sums the modified
gradients. Its discussion explicitly separates gradient conflict from the
additional roles of magnitude imbalance and curvature. This study applies that
established method to LeagueEWS shared parameters; task heads retain ordinary
gradients. The Gram-matrix implementation is tested against literal vector
projection. This is an application and mechanism test, not algorithmic novelty.
[Yu et al., Gradient Surgery for Multi-Task Learning, NeurIPS 2020, full paper](https://proceedings.neurips.cc/paper/2020/file/3fe78a8acf5fda99de95303940a2420c-Paper.pdf).

The earlier [targeted literature check](../task-sharing-2026-10-02/literature.md)
also identifies CAGrad and temporal asymmetric multitask learning. This study
does not implement or compare those alternatives, and a PCGrad failure would
not reject them. Any subsequent claim to a new transfer method would require
relevant established controls and a fresh evaluation after its final freeze.

The [discovery protocol](../../docs/league-discovery-gates.md) records prior
League temporal prediction and event-level warning work. Neither a small metric
gain nor combining known ingredients supports a first-ever claim. Related work
from other domains supplies method context only; all empirical data here are
League of Legends. This is a targeted method check, not an exhaustive survey.
