# Limits on a task sharing novelty claim

The shared versus independent comparison can identify a development result for
LeagueEWS. It cannot establish a new multitask learning method. This targeted
check of primary proceedings abstracts on 2 October 2026 is not an exhaustive
literature review or a claim to have reproduced those papers.

Yu and colleagues studied interference between task gradients and introduced
gradient surgery for multitask optimization. Merely applying a gradient
projection to LeagueEWS would reuse an established method.
[Gradient Surgery for Multi-Task Learning, NeurIPS 2020](https://proceedings.neurips.cc/paper/2020/hash/3fe78a8acf5fda99de95303940a2420c-Abstract.html).

Liu and colleagues' CAGrad uses individual tasks' local improvement to guide
optimization of their average loss. A claim that a new gradient combination
protects individual event tasks would need a relevant established comparison,
not only ordinary joint training as its control.
[Conflict-Averse Gradient Descent for Multi-task Learning, NeurIPS 2021](https://proceedings.neurips.cc/paper/2021/hash/9d27fdf2477ffbff837d73ef7ae23db9-Abstract.html).

Nguyen and colleagues model time-dependent asymmetric transfer using feature
uncertainty. Their work explicitly addresses the possibility that an improved
task average hides harm to individual tasks. Temporal or asymmetric sharing by
itself is therefore not a new research claim.
[Clinical Risk Prediction with Temporal Probabilistic Asymmetric Multi-Task Learning, AAAI 2021](https://ojs.aaai.org/index.php/AAAI/article/view/17097).

These papers motivate possible future controls; they supply no empirical League
evidence. The current experiment changes the supervision reaching an otherwise
matched encoder. If an event improves under independent training, gradient
conflict is one possible explanation, alongside loss scaling, optimization and
representation competition. No gradient intervention in this study separates
those explanations. Any mechanism chosen later must use training and early
calibration diagnostics, a separate frozen protocol and appropriate controls.

The existing [League discovery protocol](../../docs/league-discovery-gates.md)
also records related event forecasting and warning-timing work. A stronger paper
would need a specific reproducible finding, practical warning-budget performance
and an untouched evaluation after the final method is frozen. This study does
not authorize opening patch 16.17.
