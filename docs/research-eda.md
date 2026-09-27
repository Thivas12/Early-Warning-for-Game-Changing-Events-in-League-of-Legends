# Audited data atlas

Run `make render-research-eda` after final G2 validation, processed audit and
split freeze. It creates a self-contained, offline HTML report at
`reports/local/rifthazard-eda/index.html`. Open that file in a browser or print
it to PDF. No browser CDN, notebook server, Riot credential or CUDA runtime is
needed. The report is generated locally from the user's ignored private files.

The renderer first checks the G2 report, processed audit, split checksum chain,
and exact 12-cell sample. The sample matrix shows **metadata counts for all
36,000 matches**. Its event, native cadence and label-opportunity panels read
only the 24,000 training and 6,000 calibration processed matches. Every
processed file is checked against the bound processing manifest before it
contributes. The 6,000 test match files are never opened. The G2 report's
all-patch event totals are deliberately not used for the figures.

The plots explain:

- equal regional and patch allocation and the train/calibration/test boundary;
- observed Baron, Dragon and teamfight-proxy onset counts per analyzed match;
- the fraction of source events with a strictly prior genuine observation
  within each 10-, 20-, 30- and 60-second horizon;
- the minimum, median and maximum within-match observation interval.

Label opportunity is not model recall. A lack of an observation in the horizon
prevents a warning from that window even if a model's predictions at available
observations are perfect. The cadence trio is not presented as a distribution.
The figures contain aggregate counts and source checksums but no match IDs,
PUUIDs, raw payloads, individual timelines or prediction scores. Review the
locally generated HTML before copying or publishing it. The report itself is
ignored under `reports/local/` so exploratory outputs cannot silently become
a committed paper figure.
