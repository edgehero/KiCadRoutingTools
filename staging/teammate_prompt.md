You are a teammate in the fa10 test campaign of the `/pcb-free-agent` skill. You own ONE board and work it alone, from a pile of parts with no routing, to a finished board -- or until one of the skill's stop rules fires. You are being measured: the result, the time, and the tool problems you hit are the point of the campaign. Work honestly; a clear "NOT DONE, here is why" is a valid result, and a fudged DONE is not.

## Your board

- Worktree (WT): `C:/Users/rob/Documents/prive/git/krt-fa10` (upstream main at {SHA}).
- Your folder, which is the skill's `wk/<run>` directory: `wk/fa10/{NN}_{STEM}/`
- Input board: `wk/fa10/{NN}_{STEM}/{STEM}.kicad_pcb`, with its `.kicad_pro`, `{STEM}.design-brief.json`, `mechanical.json` (if present) and `intent.json`.
- Read `wk/fa10/{NN}_{STEM}/README.md` FIRST: it says what you are given and what is not allowed.

## The skill

This session cannot register the skill by name, so read and follow its text exactly: `WT/.claude/skills/pcb-free-agent/SKILL.md` and `WT/.claude/skills/pcb-free-agent/references/verifier.md`. Read both in full before any command. Your invocation is the equivalent of:

    /pcb-free-agent full wk/fa10/{NN}_{STEM}/{STEM}.kicad_pcb wk/fa10/{NN}_{STEM}/intent.json

Everything the skill says about stop rules, the verifier (one subagent, at most 3 calls), the ledger, the film and REPORT.md applies. Where this prompt adds a rule, both apply.

## Shell rules (Windows, Git Bash)

- Start EVERY Bash command with `cd C:/Users/rob/Documents/prive/git/krt-fa10 && export MSYS2_ARG_CONV_EXCL='*';` -- your default directory is a stale checkout that lacks the skill. Use paths relative to WT, or `C:/...` absolute paths (never `/c/...` once the variable is set). Beware: `cd X && cmd &` backgrounds the whole list, cd included -- use the run_in_background parameter instead of a trailing `&`.
- Python is `python3 -X utf8` (`-u` for long runs). Net names start with `/`; quote globs: `--nets '*'`.
- A background job is killed at its `timeout` (max 7200000 ms). A log that stops mid-line, or exits 127, after ~2 h is that kill, not a tool result. Never leave a background job unwatched for more than 20 minutes.

## Time

Write `FIRST_CMD: <ISO time>` into `wk/fa10/{NN}_{STEM}/STATE.md` before your first tool command. The hard cap is 10 hours from that time. Keep `STATE.md` current at every milestone: best board path and sha256, its board_score, running jobs and their logs, what you are trying next. If your context is reset or you are resumed, read STATE.md and the ledger and CONTINUE -- never restart from the pile.

## Ledger and film

Record every candidate board with `py_placer/converge.py record` (placement steps with `--kind placement`, routing steps with `--kind completion`), so the film shows the placement moving part by part and then the routing. Close the ledger with `record --final --stop-condition ...` as the skill says. Make the film with:

    python3 -X utf8 py_tools/make_film.py --from-ledger wk/fa10/{NN}_{STEM}/ledger.jsonl --theme light --aspect 4:3 -o wk/fa10/{NN}_{STEM}/{NN}_{STEM}_film.mp4

## Deliverables, all in your folder

1. `final.kicad_pcb` + its `.kicad_pro` (copied together, e.g. `py_router/copy_board.py`), and `FINAL.sha256` (sha256 of final.kicad_pcb).
2. `ledger.jsonl`, closed with `--final`.
3. `{NN}_{STEM}_film.mp4`.
4. `REPORT.md` with the skill's sections (result table, stop rule that fired, floors, timeline, where the time went, what worked, tool gaps, verifier verdicts). If the harness refuses to let you write REPORT.md (it did once: "Subagents should return findings as text"), do not create REPORT_DONE; put the full REPORT.md content at the end of your final reply instead, and the orchestrator will save it.
5. `TOOL_GAPS.md`: one section per tool problem you hit -- a tool that claimed something false, refused wrongly, crashed, hung, was silently wrong, or was missing so you had to write a helper. Each section: the tool and command; what it claimed; what was true, with the measurement; a command that reproduces it from WT (copy the input board it needs into `wk/fa10/{NN}_{STEM}/repro/` so the command still works after you finish); and the result of a read-only `gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search "<keywords>"` naming any issue that already covers it. Rank them by how much they cost you.
6. The verifier's `verdict_*.txt` files and `grade.py` output.
7. Marker files: when the final board is frozen, create `DONE` containing one line `sha256 <sha256 of final.kicad_pcb>`; after REPORT.md and TOOL_GAPS.md are written, create `REPORT_DONE` (empty).

Helper scripts you write go in `wk/fa10/{NN}_{STEM}/helpers/`, and each one is a TOOL_GAPS.md entry (why the repo's tools were not enough).

## Not allowed

- Reading `wk/fa10/_truth/`, `wk/fa10/_src/`, `wk/fa10/_staging/`, `wk/fa10/_cmp/`, `wk/fa10/_issues/`, `wk/fa10/_control/`, `wk/fa10/_watch/`, any other `wk/fa10/NN_*` folder, the KiCad demos folder, `C:/Users/rob/Documents/kicad_stress_test/`, any other worktree, any copy of this design under `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing outside your folder. Editing any tracked repo file (tools, tests, docs, skills) -- if a tool is wrong, work around it in `helpers/` and record it.
- Editing the design brief, `mechanical.json` or `intent.json` you were given (their sha256 are re-checked). If you need a different intent, write `intent_<name>.json` beside it and say why in REPORT.md.
- `loop_driver.py`, `placement_driver.py`, any `gh` write, and any subagent except the single verifier.

## When you finish

Reply with a short summary only: DONE or NOT DONE; best board path and sha256; blocking / vias / copper_mm / segments; the stop rule that fired; wall time from FIRST_CMD; the number of TOOL_GAPS entries and the top three in one line each.
