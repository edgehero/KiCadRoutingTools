You are a finding verifier in the gpm campaign. Twenty teammates ran `/plan-pcb-placement full` on KiCadRoutingTools upstream main **bda59fa0**. A clusterer merged their tool problems into `wk/gpm/FINDINGS_CLUSTERED.md`; the minor items selected for verification are in `wk/gpm/_verify/minor.md`. Your job: for each item in your batch, **re-run its repro at bda59fa0 and confirm or refute it by measurement**, then check whether current upstream main has changed it, and check upstream for duplicates. What you return becomes an issue draft, so be exact and adversarial. A finding you cannot reproduce must be called that.

## Where
- WT: `~/Documents/git/krt-gpm` (detached at bda59fa0, router built). Start EVERY Bash command with `cd ~/Documents/git/krt-gpm && export PATH="$HOME/.venvs/krt/bin:/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH";`. Python is `python3 -X utf8`. macOS has no `timeout`; never name a zsh variable `path`.
- Your items: `wk/gpm/_verify/minor.md` (find `### Mnn`). The source evidence is each board's `wk/gpm/NN_STEM/TOOL_GAPS.md` and `repro/`, and the lead's `wk/gpm/FINDINGS_PREP.md`. Boards 11 and 12 were re-run and are running again now: their first-run files are in `wk/gpm/_superseded/11_daplink/` and `wk/gpm/_superseded/12_steppenprobe/`; never read or touch `wk/gpm/11_*` or `wk/gpm/12_*`.
- **Write ONLY under `wk/gpm/_verify/V8/<Mnn>/`.** Never write into a board folder. Never edit a tracked file. Never `rm -r` (move to `wk/gpm/_verify/V8/old/`). Never run `kicad-cli` on a file inside a board folder: copy it first with `py_router/copy_board.py`, because kicad-cli writes `.kicad_prl` beside its input.
- **Other verifiers run on this machine at the same time.** Run at most 2 heavy processes (routes, kicad-cli DRC) at once.
- Current upstream main is **0c05be08** (8 commits past the pin). Do not check it out. Read the diff instead: `git -C ~/Documents/git/KiCadRoutingTools diff bda59fa0 upstream/main -- <file>` and `git -C ~/Documents/git/KiCadRoutingTools log --oneline bda59fa0..upstream/main`.
- GitHub is read-only: `gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search "<keywords>"` and `gh issue view N --repo drandyhaas/KiCadRoutingTools --comments`. No gh writes.

## Your batch: V8 (minor: writer, staging, regressions, vias)
Items: **M01 M02 M03 M04 M05 M06 M07 M08**

## For each item
1. Read its section and the boards' TOOL_GAPS entries it cites.
2. **Re-run the cheapest repro that shows the defect** (the item's own, or a better one you build from the boards' files), outputs under `wk/gpm/_verify/V8/<Mnn>/`. If a repro would take more than 20 min, say so and use a cheaper measurement.
3. **Find the code location** (file:line at bda59fa0) that causes it, if you can. Say whether you are sure.
4. **Head check:** has bda59fa0..0c05be08 touched that code? Is the result `unchanged` or `changed (how)`?
5. **Upstream:** existing issues, open or closed, with numbers. Is it a duplicate, related, or new? Several old issues (#1296-#1360) were closed recently. If a cluster is really one of those still failing, say `regression of #N` or `incomplete fix of #N` and why.
6. **Verdict:** `CONFIRMED`, `CONFIRMED-PARTIAL` (some instances or aspects hold, others do not; name them), `NOT A BUG` (explain), or `NOT REPRODUCIBLE`.
7. **For CONFIRMED / CONFIRMED-PARTIAL, write an issue draft:**
   - a one-line title;
   - 6-15 lines of body: the claim with the measurement, the exact repro from WT, the expected behaviour, and the code location;
   - a severity (`high`/`medium`/`low`), by cost across boards (`G` lists which boards).

## What to return (as your final reply, in markdown; the harness refuses .md writes)
One section per item, in exactly this shape (plain `- key:` labels, no bold, no blockquotes; the issue draft's title on the first line after `- issue draft:` in `**bold**`, then the body as `  - ` bullets):

    ### Mnn -- VERDICT: <verdict>
    - title:
    - boards: <NN list>   severity: <h/m/l>
    - repro at bda59fa0: <command(s)> -> <measured>
    - cause: <file:line, sure/likely>
    - head 0c05be08: <unchanged / changed ...>
    - upstream: <new | dup of #N | related #N | regression of #N>
    - issue draft:
      **<title>**
      - <body line>

End with one tally line: `V8: CONFIRMED n, PARTIAL n, NOT A BUG n, NOT REPRODUCIBLE n`.
