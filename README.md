# gpm campaign assets: 20 boards through `/plan-pcb-placement full` on KiCadRoutingTools main bda59fa0

Results are in discussion #118 (drandyhaas/KiCadRoutingTools). This branch holds what the post links to.

- `media/NN_STEM/`: per board:
  - the movie3d films (`film_seed.*`, the kept seed's anneal; `film_flow.*`, the whole run, where it tells the run's story);
  - the 3D stills, and the human-vs-ours placement comparisons;
  - the teammate's `REPORT.md`, `TOOL_GAPS.md` and `CHOSEN.json`;
  - what it was given (`README.md`);
  - my grades (`summary.json`, `grade_ours.json`, `board_score.json`);
  - the delivered board.
- `media/_superseded/`: the first runs of daplink and steppenprobe, which were re-run after the audit.
- `wk/gpm/`: every `wk/gpm/...` path the findings and issues cite, at the same path. Copy `wk/` into a checkout at bda59fa0 and run the repro commands from the root.
- `FINDINGS.md`: every verifier verdict (G01-G47, M01-M16). `FINDINGS_CLUSTERED.md` holds the clusters before verification, and `verify/` the batch reports and prompts.
- `old_issues/`: gp14's 65 issues re-checked on main (`OLD_ISSUES.md`, `B1.md`-`B8.md`).
- `AUDIT.md` and `audit/`: the start-state, copying and transcript audit, with its scripts and outputs.
- `issues/`: the issue drafts as filed.
- `staging/`: the campaign scripts (staging, teammate prompt, compare, films, post).
- `GRADE_NOTES.md`, `LAUNCH.md`, `PHASE0.md`, `STAGING_DIFF.md`, `FINDINGS_PREP.md`: the lead's own notes.
