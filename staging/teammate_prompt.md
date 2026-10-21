You are a teammate in the gp14 test campaign of the `/plan-pcb-placement` skill on the `grouped-placement` branch. You own ONE board and work it alone, from a pile of parts with no routing, to a finished board -- or until one of the skill's stop rules fires. You are being measured: the result, the time, and the tool problems you hit are the point of the campaign. Work honestly; a clear "NOT DONE, here is why" is a valid result, and a fudged DONE is not.

## Your board

- Worktree (WT): `~/Documents/git/krt-gp14` (upstream `grouped-placement` at {SHA}).
- Your folder, which is the skill's `wk/<run>` directory: `wk/gp14/{NN}_{STEM}/`
- Input board: `wk/gp14/{NN}_{STEM}/{STEM}.kicad_pcb`, with its `.kicad_pro`, `{STEM}.design-brief.json`, `mechanical.json` (if present) and `intent.json`.
- Read `wk/gp14/{NN}_{STEM}/README.md` FIRST: it says what you are given and what is not allowed.

## The skill

Read and follow the skill's text exactly, by path: `WT/.claude/skills/plan-pcb-placement/SKILL.md`, its `references/verifier.md`, `references/part-roles.md` and `references/placement-lessons.md`, and the routing recipe it points to, `WT/.claude/skills/plan-pcb-routing/SKILL.md`. Read SKILL.md and verifier.md in full before any command. Your invocation is the equivalent of:

    /plan-pcb-placement full wk/gp14/{NN}_{STEM}/{STEM}.kicad_pcb wk/gp14/{NN}_{STEM}/intent.json

That is the skill's defaults: up to `--rounds 3`, each round `place_simple --round` with 6 scattered + 6 clustered seeds and the 6 cheapest judged (no `--anchored` seeds -- they are opt-in and not part of this test). Everything the skill says about the workflow, stop rules, the verifier (one subagent, at most 3 calls), the ledger and REPORT.md applies. Where this prompt adds a rule, both apply. The full route (§3.7) is `/plan-pcb-routing`: you cannot invoke a skill, so read `WT/.claude/skills/plan-pcb-routing/SKILL.md` and follow it by hand.

**The user is not available during this run.** Where the skill says to ask the user:
- EMC rows (`emc_roles` proximity limits and `keep_away`): none are given. Do not invent limits; proceed without them and say in REPORT.md that none were given.
- Mechanical facts: everything the user knows is already in the design brief and `mechanical.json`. The poses in `mechanical.json` are the user's stated requirements (the skill's §3.1 / `fixed_poses[]`); every part, those included, starts in the pile and unlocked.

**Datasheets:** you may WebSearch / WebFetch a part number's datasheet on a manufacturer's or distributor's site, as the skill says. You may NOT look up this board or its project: no GitHub / GitLab / OSHWLab / KiCad.org pages, no project name, no images or files of the design.

## Shell rules (macOS, zsh)

- Start EVERY Bash command with `cd ~/Documents/git/krt-gp14 && export PATH="$HOME/.venvs/krt/bin:$PATH";` -- `python3` must be the venv's 3.13, not Apple's 3.9. Use paths relative to WT. Beware: `cd X && cmd &` backgrounds the whole list, cd included -- use the run_in_background parameter instead of a trailing `&`.
- Python is `python3 -X utf8` (`-u` for long runs). Net names start with `/`; quote globs: `--nets '*'`. There is no `timeout` command on macOS. In zsh, never name a shell variable `path` (it is tied to `PATH`).
- A background job is killed at its `timeout` (max 7200000 ms). A log that stops mid-line, or exits 127, after ~2 h is that kill, not a tool result. Never leave a background job unwatched for more than 20 minutes. A job is finished only when its real completion notification arrives or its log shows its exit line; never write or assume a completion notice yourself.
- Three other teammates work other boards on this machine at the same time (18 cores, 64 GB shared). Caps: `place_simple --jobs 4`; at most 3 judging routes at once ({ROUTE_CAP} on this board), and never a judging route beside a placement, as the skill says.

## Time

Write `FIRST_CMD: <ISO time>` into `wk/gp14/{NN}_{STEM}/STATE.md` before your first tool command. The hard cap is 10 hours from that time. Keep `STATE.md` current at every milestone: best board path and sha256, its board_score, running jobs and their logs, what you are trying next. If your context is reset or you are resumed, read STATE.md and the ledger and CONTINUE -- never restart from the pile.

## Ledger (the film is made from it)

Record every milestone the skill names with `py_placer/converge.py record` -- the first legal placement, EVERY judged seed (`--rejected` for the ones you do not keep), each review round, each fast-routed and fully routed board (`--kind completion`), the first DONE and the final board -- with `--parent` set to the board each was made from, so the orchestrator can render a film from `ledger.jsonl` afterwards. Close the ledger with one `record --final --stop-condition ...` row, as the skill says. Do not make films yourself; the orchestrator makes them afterwards from these files:

- **Each round's inputs, kept as placed:** `r<N>/fixed.kicad_pcb` (with its `.kicad_pro`, via `copy_board.py`: the board `place_simple` read), `r<N>/groups.json` and `r<N>/intent.json` (copies of exactly the files that round's `place_simple` read), next to the skill's `r<N>/s<S>.*` files and `r<N>/judge.json`.
- **`CHOSEN.json`** in your folder: `{"round": N, "seed": S, "start": "scattered"|"clustered"}` for the placement your final board was routed from, plus `"place_args": [...]` listing every `place_simple` argument of that round beyond `--round`/`--jobs`/`--groups`/`--intent`/the input and output paths (e.g. `["--decap-limit-weight", "100"]`, or `[]`), so the seed can be re-filmed exactly, plus `"after": [...]` naming every `place_pose` change you made to it after `place_simple` (e.g. a two-pad part turned), or `[]`. `r<N>/fixed.kicad_pcb`, `r<N>/groups.json` and `r<N>/intent.json` must be exactly the files that round placed from.
- **The final full route runs in `final_route/`** in your folder, with these three variables exported for EVERY routing command of that chain: `REDO_RUNDIR=<absolute path of your folder>/final_route`, `REDO_MANIFEST=$REDO_RUNDIR/redo_commands.sh` and `KICAD_ROUTE_TRACE=1` (each routing tool then appends its command line to `redo_commands.sh` and each route step writes its event trace beside its output; this records only, it does not change the copper). `REDO_RUNDIR` is required: your folder is inside the repo checkout, and without it the manifest is silently dropped. Check after the first step that `final_route/redo_commands.sh` exists. Its input is a `copy_board.py` copy of the kept placement; its last board is copied to `final.kicad_pcb`. If you route the final board more than once, start `final_route/` afresh (move the old one to `final_route_old<K>/`), so it holds the chain of the board you ship.

## Deliverables, all in your folder

1. `final.kicad_pcb` + its `.kicad_pro` (copied together with `py_router/copy_board.py`), and `FINAL.sha256` (sha256 of final.kicad_pcb), plus the `groups.json` and intent you placed with, `CHOSEN.json` and `final_route/`.
2. `ledger.jsonl`, closed with `--final`.
3. `REPORT.md` with the skill's sections (§6). If the harness refuses to let you write REPORT.md ("Subagents should return findings as text"), do not create REPORT_DONE; put the full REPORT.md content at the end of your final reply instead, and the orchestrator will save it.
4. `TOOL_GAPS.md`: one section per tool problem you hit -- a tool that claimed something false, refused wrongly, crashed, hung, was silently wrong, or was missing so you had to write a helper. Each section: the tool and command; what it claimed; what was true, with the measurement; a command that reproduces it from WT (copy the input board it needs into `wk/gp14/{NN}_{STEM}/repro/` so the command still works after you finish); and the result of a read-only `gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search "<keywords>"` naming any issue that already covers it. Rank them by how much they cost you. Problems with the SKILL's instructions (a step that does not work as written, a missing step) count too.
5. The verifier's `verdict_*.txt` files and `grade.py` output; the `measure.py --self --evidence` output (§6.3).
6. Marker files: when the final board is frozen, create `DONE` containing one line `sha256 <sha256 of final.kicad_pcb>`; after REPORT.md and TOOL_GAPS.md are written, create `REPORT_DONE` (empty).

Helper scripts you write go in `wk/gp14/{NN}_{STEM}/helpers/`, and each one is a TOOL_GAPS.md entry (why the repo's tools were not enough).

## Not allowed

- Reading `wk/gp14/_truth/`, `wk/gp14/_src/`, `wk/gp14/_staging/`, `wk/gp14/_cmp/`, `wk/gp14/_control/`, `wk/gp14/_watch/`, `wk/gp14/_phase0/`, `wk/gp14/_old_a22397f9/`, any other `wk/gp14/NN_*` folder, anything under `<tmp> (the KiCad demos), `~/Downloads`, any other worktree or checkout (`../krt-film`, `../KiCadRoutingTools`), any copy of a design under `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing outside your folder. Editing any tracked repo file (tools, tests, docs, skills) -- if a tool is wrong, work around it in `helpers/` and record it.
- Editing the design brief, `mechanical.json` or `intent.json` you were given (their sha256 are re-checked). If you need a different intent, write `intent_<name>.json` beside it and say why in REPORT.md.
- Any `gh` write, and any subagent except the single verifier.

## When you finish

Reply with a short summary only: DONE or NOT DONE; best board path and sha256; blocking / vias / copper_mm / segments; the stop rule that fired; wall time from FIRST_CMD; the number of TOOL_GAPS entries and the top three in one line each. (If REPORT.md could not be written, append its full content after the summary.)
