You are a teammate in the gpm test campaign of the `/plan-pcb-placement` skill on upstream **main** (grouped placement merged, v0.23.7). You own ONE board and work it alone. You start from a pile of parts with no routing, and you finish with a finished board, or stop when one of the skill's stop rules fires. You are being measured: the result, the time, and the tool problems you hit are the point of the campaign. Work honestly. A clear "NOT DONE, here is why" is a valid result; a fudged DONE is not.

## Your board

- Worktree (WT): `~/Documents/git/krt-gpm`, which is upstream `main` at bda59fa0.
- Your folder: `wk/gpm/17_environment_sensor/`. This is the skill's `wk/<run>` directory.
- Input board: `wk/gpm/17_environment_sensor/environment_sensor.kicad_pcb`. With it come its `.kicad_pro`, its `.kicad_dru` (if present), `environment_sensor.design-brief.json`, `mechanical.json` (if present) and `intent.json`.
- Read `wk/gpm/17_environment_sensor/README.md` FIRST. It says what you are given and what is not allowed.

## The skill

Read the skill's text by path and follow it exactly:
- `WT/.claude/skills/plan-pcb-placement/SKILL.md`;
- its `references/verifier.md`, `references/part-roles.md` and `references/placement-lessons.md`;
- the routing recipe it points to, `WT/.claude/skills/plan-pcb-routing/SKILL.md`.

Read SKILL.md and verifier.md in full before any command. Your invocation is the equivalent of:

    /plan-pcb-placement full wk/gpm/17_environment_sensor/environment_sensor.kicad_pcb wk/gpm/17_environment_sensor/intent.json

That means the skill's defaults: one pass of 12 seeds (6 scattered, 6 clustered), with the 6 the objective rates best judged by `py_placer/judge_seeds.py`. Anchored seeds are opt-in and not part of this test. Everything the skill says applies, all the way to §3.9's `delivered.kicad_pcb`: the workflow including §3.5's datasheet templates, the stop rules, the verifier (one subagent, at most 3 calls), the ledger and REPORT.md. Where this prompt adds a rule, both apply.

You cannot invoke a skill, so follow every skill the recipe names by hand, from its SKILL.md. That covers the full route (§3.8 = `/plan-pcb-routing`) and the `/analyze-power-nets` step that plan-pcb-routing now asks for. For each, write in REPORT.md that you followed it by hand.

**The intent you were given is read-only.** `intent.json` already compiles the design brief and `mechanical.json`, so do not emit another (§3.2: a given intent is the intent). Some skill steps write an intent: `waive_locked_overlaps.py`, `fit_template.py --write-intent`, an `overlap_waivers[]` or `proximity[]` row you add. Before the first of them, copy `intent.json` to `intent_run.json`, then use `intent_run.json` for every later step, placing, judging, scoring and the verifier included. REPORT.md lists every row you added to it, with the reason. `fixed.kicad_pcb` is a `copy_board.py` copy of the input board. Nothing in it is locked, and the declared poses reach place_simple through the intent's `fixed_poses[]`.

**The user is not available during this run.** Where the skill says to ask the user:
- **EMC rows** (`emc_roles` proximity limits and `keep_away`): none are given. Do not invent limits. Proceed without them, and say in REPORT.md that none were given.
- **Mechanical facts:** everything the user knows is already in the design brief and `mechanical.json`. The poses in `mechanical.json` are the user's stated requirements (the skill's §3.1 / `fixed_poses[]`). Every part starts in the pile and unlocked, those included.
- **A choice the skill leaves to the user** (for example which of two locked parts to move): make it yourself, and record it in REPORT.md as a judgment.

**Datasheets** (§3.5 templates, analyze-power-nets):
- You may WebSearch / WebFetch / curl a part number's datasheet from a manufacturer's or distributor's site.
- You may NOT look up this board or its project. That rules out GitHub / GitLab / OSHWLab / KiCad.org pages, the project's name, and any image or file of the design.

## Shell rules (macOS, zsh)

- Start EVERY Bash command with `cd ~/Documents/git/krt-gpm && export PATH="$HOME/.venvs/krt/bin:$PATH";`. `python3` must be the venv's 3.13, not Apple's 3.9. Use paths relative to WT.
- Beware that `cd X && cmd &` backgrounds the whole list, cd included. Use the run_in_background parameter instead of a trailing `&`.
- Python is `python3 -X utf8` (add `-u` for long runs).
- Net names start with `/`, so quote globs: `--nets '*'`.
- There is no `timeout` command on macOS. In zsh, never name a shell variable `path` (it is tied to `PATH`).
- **Never run `rm -r` or `rm -rf`, nor a delete of a directory.** In the last campaign such a call sat on a permission prompt for 2 hours. To get rid of something, move it into your folder's `old/` with `mv`. That includes the skill's §6.4 "datasheet folder deleted": move `datasheets/` to `old/datasheets/`, and the orchestrator deletes it.
- A background job is killed at its `timeout` (max 7200000 ms). A log that stops mid-line, or exits 127, after about 2 h is that kill, not a tool result.
- Never leave a background job unwatched for more than 20 minutes. A job is finished only when its real completion notification arrives or its log shows its exit line. Never write or assume a completion notice yourself.
- **Three other teammates work other boards on this machine at the same time** (18 cores, 64 GB shared). Caps:
  - `place_simple --jobs 4`;
  - `judge_seeds.py --jobs 3` on this board;
  - at most 3 routing processes of yours at once;
  - never a judging route beside a placement of yours.

## Time

- Write `FIRST_CMD: <ISO time>` into `wk/gpm/17_environment_sensor/STATE.md` before your first tool command. The hard cap is 10 hours from that time.
- Keep `STATE.md` current at every milestone: the best board's path and sha256, its board_score, running jobs and their logs, and what you are trying next.
- If your context is reset or you are resumed, read STATE.md and the ledger and CONTINUE. Never restart from the pile.

## Files the orchestrator films and grades (keep them exactly)

- **The seeds stay where the skill puts them:** `s<S>.kicad_pcb/.json/.log`, `s<S>_route/`, `s<S>_fast.kicad_pcb` and `s<S>_fast.score.json`, plus `judge.json` and `judge_chain.txt`, in your folder.
- **Export `KICAD_ROUTE_TRACE=1` for every `judge_seeds.py` run.** It only records each route step's events beside its board; it does not change the copper.
- **`placed_from/`** holds exactly the files the pass that produced your kept seed read: `fixed.kicad_pcb` (with its `.kicad_pro`, via `copy_board.py`), `groups.json` and the intent file. Keep that intent file's own name.
- **Placing again** (a new pass of §3.6) overwrites the seeds. Before it, `mv` the previous pass's `s*` files, `judge.json`, `judge_chain.txt` and `placed_from/` into `old/pass<K>/`.
- **`CHOSEN.json`**, in your folder, has these keys:
  - `"seed"`: S, the kept seed;
  - `"start"`: `"scattered"` or `"clustered"`;
  - `"pass"`: K;
  - `"intent"`: the intent file the pass placed with;
  - `"place_args"`: every `place_simple` argument of that pass beyond the input, OUT, `--groups`, `--intent`, `--jobs` and `--json` (e.g. `["--template-weight", "200"]`, or `[]`). With it, the seed can be re-filmed exactly.
  - `"after"`: every `place_pose` change you made to it after `place_simple` (e.g. a two-pad part turned on route_review's advice), or `[]`.
- **The full route (§3.8) runs in `final_route/`.** Its input is a `copy_board.py` copy of your `final.kicad_pcb` (the kept placement), named `final_route/in.kicad_pcb`.
  - Export three variables for EVERY routing command of that chain: `REDO_RUNDIR=<absolute path of your folder>/final_route`, `REDO_MANIFEST=$REDO_RUNDIR/redo_commands.sh` and `KICAD_ROUTE_TRACE=1`. `REDO_RUNDIR` is required: your folder is inside the repo checkout, and without it the manifest is silently dropped.
  - After the first step, check that `final_route/redo_commands.sh` exists.
  - The chain's last board is copied with `copy_board.py` to `routed.kicad_pcb` in your folder. That is the board §3.9 starts from.
  - If you route the final board more than once, move the old `final_route/` to `final_route_old<K>/` first, so `final_route/` holds the chain of the board you ship.

## Ledger

Record every milestone the skill names (§5 rule 6) with `py_placer/converge.py record`, `--parent` set to the board it was made from:
- the first legal placement;
- EVERY judged seed (`--rejected` for the ones you do not keep);
- the kept placement;
- the first routed board and each further fully routed board (`--kind completion`);
- the first DONE;
- the delivered board.

Close the ledger with one `record --final --stop-condition ...` row, as the skill says.

## Deliverables, all in your folder

1. **The boards.**
   - `delivered.kicad_pcb` with its `.kicad_pro` (via `copy_board.py`). In full mode the skill hands back §3.9's filled board; if `fill_for_delivery` failed, copy the unfilled board here and say so.
   - `DELIVERED.sha256`, holding the sha256 of delivered.kicad_pcb.
   - `routed.kicad_pcb` and `final.kicad_pcb` (the kept placement).
   - `groups.json`, the intent files, `CHOSEN.json`, `placed_from/` and `final_route/`.
2. **`ledger.jsonl`**, closed with `--final`.
3. **`REPORT.md`**, with the skill's §6 sections. If the harness refuses to let you write it ("Subagents should return findings as text"), do not create REPORT_DONE. Put the full REPORT.md content at the end of your final reply instead, and the orchestrator will save it.
4. **`TOOL_GAPS.md`**: one section per tool problem you hit, ranked by how much it cost you.
   - **What counts:** a tool that claimed something false, refused wrongly, crashed, hung, was silently wrong, or was missing so you had to write a helper. Problems with the SKILL's instructions count too: a step that does not work as written, or a missing step.
   - **Each section gives:**
     - the tool and command;
     - what it claimed;
     - what was true, with the measurement;
     - a command that reproduces it from WT. Copy the input board it needs into `wk/gpm/17_environment_sensor/repro/`, so the command still works after you finish.
     - the result of a read-only `gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search "<keywords>"`, naming any issue (open or closed) that already covers it.
5. **Verifier and grading output:**
   - the verifier's `verdict_*.txt` files;
   - the `grade.py` output;
   - the `measure.py --self --evidence` output (§6.3).
6. **Marker files:**
   - when the delivered board is frozen, create `DONE` containing one line, `sha256 <sha256 of delivered.kicad_pcb>`;
   - after REPORT.md and TOOL_GAPS.md are written, create `REPORT_DONE` (empty).

Helper scripts you write go in `wk/gpm/17_environment_sensor/helpers/`. Each one is a TOOL_GAPS.md entry that says why the repo's tools were not enough.

## Not allowed

- **Reading:**
  - in `wk/gpm/`: `_truth/`, `_src/`, `_staging/`, `_cmp/`, `_control/`, `_watch/`, `_phase0/`, `_oldissues/`, `_verify/`, and any other `wk/gpm/NN_*` folder;
  - `wk/gp14/`;
  - other checkouts and worktrees: `../krt-gp14`, `../gp14-assets`, `../krt-film`, `../KiCadRoutingTools`;
  - anything under `<tmp>` (the KiCad demos), and `~/Downloads`;
  - any copy of a design under `kicad_files/`, `tests/fixtures/` or a stress-corpus folder;
  - git history of board files;
  - GitHub discussion #118.
  Reading an issue's title in a `gh issue list` search is fine. Do not open the bodies of #1296-#1360: they describe these boards from an earlier campaign.
- **Writing** outside your folder, and editing any tracked repo file (tools, tests, docs, skills). If a tool is wrong, work around it in `helpers/` and record it.
- **Editing** the design brief, `mechanical.json` or `intent.json` you were given; their sha256 are re-checked.
- **Any `gh` write**, and any subagent except the single verifier.

## When you finish

Reply with a short summary only:
- DONE or NOT DONE;
- the delivered board's path and sha256;
- blocking / joins_needed / vias / copper_mm / segments;
- the stop rule that fired;
- the wall time from FIRST_CMD;
- the number of TOOL_GAPS entries, and the top three in one line each.

If REPORT.md could not be written, append its full content after the summary.
