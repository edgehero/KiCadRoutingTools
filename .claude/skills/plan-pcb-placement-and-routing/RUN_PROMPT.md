# Run prompt — place and route one board, provably

Copy everything below the line. Replace `<BOARD>` and `<RUN>`. Nothing else needs
changing, and no other context is required.

---

Place and route `<BOARD>` using `/plan-pcb-placement-and-routing`. Work in
`wk/<RUN>/`.

**Ask the driver for one stage at a time and follow its refusals.** An `<error>`
means a gate is holding: produce what it asks for rather than working around it.

```bash
D=.claude/skills/plan-pcb-placement-and-routing/scripts/loop_driver.py
python3 -X utf8 $D --stage L1 --board <BOARD> --ledger wk/<RUN>/ledger.jsonl
```

**Read the board's own floor first** (`.kicad_pro` Default netclass, `.kicad_dru`)
and pass it to every checker. `check_assembly` defaults to 0.25, `check_channels`
to `--track-width 0.3`, and neither reads the board — a default has invented
defects that cost whole runs. `check_drc` skips pad-to-board-edge without
`--check-pad-edge`. Record the floor before anything runs: the DRC writeback
lowers it in outputs, so grade the final board against the ORIGINAL.

**Spawn three watchers BEFORE the first stage**, as `general-purpose` agents.
Each gets `wk/<RUN>/` and the ledger, each writes to its own FILE, each is
re-invoked at every accepted step. Every entry: reference, what was measured,
what was claimed, the command to reproduce, a disposition. **Silence is not a
pass** — say what you checked even when it held.

- **EVIDENCE → `audit.md`** — does every claim match its artefact *now*? Re-read
  each region every round; never carry a line number across rounds. Flag
  truncated reads summarised as complete, renders produced but never read, and
  journal entries written after the fact.
- **TOOLS → `findings.md`** — where did an instrument lie, hang or go quiet?
  Shell codes (124/143/126/127) worn as a tool's verdict, a missing
  `JSON_SUMMARY`, a step with no bound, grading at a floor the board was not
  routed to. **Never scrape the last `JSON_SUMMARY`** — count them and read each
  one's `scope`.
- **LOOP → `loopcheck.md`** — verify control flow from the logs and ledger, not
  from anyone's account: every stage *invoked* (not merely its work done); both
  halves really delegated (a prompt emitted **and** an agent spawned); every path
  the driver named exists and the next stage opened on it; every accepted lap
  recorded and every rejected one recorded with `--rejected`.

**Both inner halves go to a teammate**, spawned as `claude` or
`general-purpose` — never `Explore` or `Plan`, which cannot spawn their own
verifiers. Use the driver's `<subagent_prompt>` verbatim and the paths it names.

**Tee every stage invocation** (`tee -a wk/<RUN>/logs/stages.log`). A watcher
cannot credit work whose invocation was never recorded, and `tee` without `-a`
destroys the previous one.

**Bound every searching step** with `--deadline`, below the smallest cap in your
stack, and run long ones detached rather than raising it. A tool that does not
terminate is a RESULT — report it. On deadline, several tools leave the partial
board at `<output>.staging.kicad_pcb` and say so only on stderr.

**Classification decides who fixes it.** `parameter` is the routing half's own;
`placement` and `floorplan` end its turn and come back to you for L3 then L4.
Run `check_reachability` on the COPPER-FREE board — on a routed board a `CAGED`
verdict means the router's own copper — and read its exit code, not the JSON
`verdict` alone.

**On Windows/Git Bash**: `export MSYS2_ARG_CONV_EXCL='*'` before any command
carrying net names (every KiCad net name starts with `/` and gets silently
rewritten into a path). It also breaks real paths, so pass those Windows-style.

## Deliver, in `wk/<RUN>/`

1. **The board** — final `.kicad_pcb` WITH its `.kicad_pro`, sha256 of both.
2. **The film** — `make_film.py --from-ledger wk/<RUN>/ledger.jsonl -o
   wk/<RUN>/film.gif`. If the placement beats are stills, nothing moved: say so.
3. **`REPORT.md`** — lead with `blocking` (`unrouted + broken` first). Will it
   build? Grade against the board's ORIGINAL floor with two instruments, since
   they disagree. Against a human reference if one exists — compare copper
   length, vias, smallest via, per-layer copper; **never segment counts** (the
   parser tessellates arcs). Say which stages fired and whether both halves were
   delegated, from `loopcheck.md`.
4. **`journal.md`** — numbered, written as you go, each entry carrying its
   measurement and the command that produced it.
5. **`audit.md` + `findings.md` + `loopcheck.md`**, dispositioned, each
   headlined in the report.

**A claim you cannot reproduce is not a result.** List, in the report, anything
you could not verify — your own claims first.
