# M1 event-specific hazard contract

The registered labels ask whether **each** of Baron, Dragon and a qualifying
teamfight begins strictly after a genuine timeline observation and no later
than 10, 20, 30 or 60 seconds. More than one event type can occur within the
same window or even the same 10-second bin. A single mutually exclusive
competing-risk softmax would erase later or simultaneous event types and could
not reproduce all twelve registered targets. The correction is recorded in
`docs/protocol-amendments.md`; the original `configs/rifthazard-v2.yaml` is
retained as the historical registration, and the executable supplement is
`configs/rifthazard-m1-hazards.yaml`.

For each observation, `event_hazard_targets` finds the **first strictly future**
onset of each type separately. It returns a 3 × 6 tensor, ordered Baron,
Dragon, teamfight, with a one in the 10-second interval containing that onset
and zeros otherwise. An event exactly at the observation timestamp is excluded;
an event at the interval's upper boundary is included. Events beyond 60
seconds and types with no future event have all-zero rows. Each target row
trains a separate conditional hazard while the match is at risk for that
event type; after its first onset, later bins of that type are masked in the
likelihood. Other types remain at risk. A first event followed by another
onset of the same type within the 60-second window does not alter the binary
``any event by horizon`` target.

At inference, each type has six sigmoid hazards in [0, 1]. Its cumulative
risk at bin k is `1 - product(1 - hazard_i)` over bins 1 through k. Read bins
1, 2, 3 and 6 for the registered horizons. This enforces within-type
monotonicity and does not constrain risks of different event types to sum to
one. The independent-horizon-head ablation, Brier comparison and B3 primary
comparator are unchanged. This contract establishes targets and interpretation
only; it does not fit M1, score calibration or access the final test patch.
