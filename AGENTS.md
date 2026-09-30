# Research scope

The user confirmed on 30 September 2026 that this project is exclusively about
League of Legends. This instruction applies to research choices, experiments,
reports and descriptions of progress throughout this repository.

- Use League of Legends data for empirical claims about this project. Do not
  substitute Dota, another game, or synthetic examples when League data are
  unavailable. Report the access limitation and prepare the concrete next step.
- Baron and Dragon labels currently identify objective kills/completions, not
  first damage or engagement onset. Use the definitions in `src/league_ews/labels.py`.
- Preserve the audited train/calibration split and the sealed patch-16.17 test.
  Reading test membership metadata does not authorize reading test payloads.
- Calibration results already inspected are exploratory. Unit tests and synthetic
  demonstrations are implementation checks, not empirical League findings.
- The historical Dota work is out of scope. Do not acquire more Dota data, run its
  experiments, present its metrics as League progress, or use it to support a
  League novelty claim. Keep its frozen artifacts for provenance; do not silently
  rewrite them. The user must explicitly reopen that separate direction.
- Do not claim access to the user's WSL filesystem, CUDA device, private cache,
  or a completed training run unless verified in the active execution environment.

Read `docs/league-research-scope.md` for the current evidence and access boundary.
