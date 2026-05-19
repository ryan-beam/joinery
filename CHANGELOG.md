# Changelog

All notable changes to Joinery are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — roborev findings surfacing layer (audit-driven port #6)

Closes the gap left by PR #20: roborev was correctly wired but intentionally does not surface findings to the developer beyond writing to its SQLite store at `~/.roborev/reviews.db`. Without an active surfacing layer, the pre-push hook would block on findings but the user wouldn't know findings existed until they tried to push. The framework owns this surfacing — that's what's new here.

**`src/joinery/roborev.py` — new Python query module.** Pure-Python (no `jq` dependency) wrapper around `roborev show <sha> --json`. Public API: `is_available()`, `query_findings(shas)`, `summarize(findings) -> FindingsSummary`, `format_summary(summary) -> str`. Graceful: returns empty results if `roborev` isn't on PATH. The pre-push hook keeps its parallel `bash + jq` implementation because it runs in a pure-shell context; this module is the Python twin for hook scripts + skills.

**SessionStart hook (`templates/session_start_hook.py.template`) — surfaces findings at every session start.** New `_branch_commits()` resolves commits on the current branch but not yet on `origin/<main>` (capped at 20 to bound subprocess calls). New `_roborev_findings_summary()` walks those commits, queries roborev for unresolved critical/high findings per commit, and emits a one-line summary like `"2 critical, 1 high unresolved (commits abc1234, def5678)"` injected into the orientation context. Silent fallback if roborev isn't installed. Without this, roborev was firing reviews silently into the SQLite store — findings invisible until the user happened to run `roborev tui`.

**`workshop session end` Phase 1 gate.** Phase 1 used to gate only on red tests. It now ALSO gates on unresolved roborev critical/high findings on the branch. Bash + jq snippet in the skill prompt mirrors the pre-push hook's query pattern. Graceful: if roborev isn't on PATH, the gate is skipped silently. The Phase 1 hard rule was extended accordingly. The skill description now mentions the roborev gate so auto-invocation triggers stay accurate.

**Phase 4 (production-tier merge gate) — stale `reviews/<sha>.md` reference fixed.** The Phase 4 prose still pointed at "no `reviews/<sha>.md` file exists" as the unreviewed-commit test — a leftover from before PR #20 corrected the integration. Roborev's data lives in SQLite, not a markdown file. Phase 4 now branches: if roborev is installed, query `roborev show <sha> --json` and refuse the merge on unresolved critical/high; if roborev isn't installed, fall back to the framework's built-in `/review` skill (which still writes `reviews/<sha>.md` for record-keeping in the no-roborev path).

**Tests (`tests/test_roborev.py`):** 19 new tests covering `is_available` (PATH miss, version probe success/failure, subprocess exception), `query_findings` (parses critical/high, drops resolved/dismissed/fixed, falls through `severity → level`, treats missing status as `open`, swallows empty stdout / malformed JSON / subprocess exceptions, dedupes repeated SHAs), `summarize` (severity counts, affected-sha collection, empty-input handling), `format_summary` (empty input → empty string, critical ordered first, sha truncation at 5). `BLOCKING_SEVERITIES` constant is locked under test to keep gate semantics synchronized with the pre-push hook.

**Net result:** every roborev finding is now visible at session start, gates session-end Phase 1, and (if blocking) refuses merge in Phase 4. The framework's "adversarial review actually changes behavior" loop is closed.

### Added — `/review` isolated subagent engine (audit-driven port #6)

Closes the partial-fix flagged in `docs/audits/obra-superpowers-2026-05-18.md` for hole #1 (subagent-isolated review). Before this PR, when roborev wasn't installed the `/review` skill fell back to the Claude Code built-in `/review` running in the *current session* — which sees the implementer's prior conversation, TODO comments, plan.md, open side quests. Reviews from a contaminated context aren't adversarial; they're agreement.

**Engine cascade restructured around isolation strength, not just tool availability:**

1. **roborev** (preferred — separate process, full isolation)
2. **Isolated Claude Code subagent (NEW)** — `Task` tool spawns a fresh-context reviewer that sees ONLY the diff + tier + reviewer prompt. No project context, no conversation history, no implementer reasoning.
3. **Claude Code built-in `/review`** — runs in-session, less isolation
4. **External `claude code -p` subprocess** — last resort

The skill prompt now includes the exact reviewer-subagent prompt template, deliberately stripped of any context about the implementer's reasoning. The reviewer sees the code and grades against tier-calibrated severity (production = strict, sketch = lenient). Output marks which engine produced the review in a new `Engine:` header on `reviews/<sha>.md` — future readers can weigh findings by isolation guarantee.

**New config key `[review] use_isolated_subagent`:**
- `production` — `true` (review honesty matters; isolation is non-negotiable)
- `standard` — `true` (same)
- `sketch` — `false` (review ceremony fights exploration speed; sketches that want review can fall through to engines C/D manually)

**Tests:** 3 new in `tests/test_init.py` covering tier-appropriate defaults landing in scaffolded configs. The pre-push hook + `/review` skill both depend on the config key existing; the parametrized test locks this in.

**Spec §12** restructured to describe the four-engine cascade and explain why ordering is by isolation strength, not tool availability.

This is audit-driven port #6 of 10 from the May 18 obra/superpowers audit. PRs 1-5 shipped 2026-05-18 (#15-19). PR #21 (surfacing layer) is the 6th shipped overall but wasn't on the original 10-PR audit list. 4 audit ports remain after this: `/execute-plan`, `/swarm`, tier-gated `/tdd`, `writing-skills`+`receiving-review`.

### Added — final 4 audit-driven ports close out the obra/superpowers porting plan

This PR ships the remaining 4 of 10 ports from `docs/audits/obra-superpowers-2026-05-18.md`. With this merged, the audit-driven porting work surfaced during the 2026-05-18 placket-ops dogfood is complete (ports 1-6 shipped in PRs #15-19 + #22; ports 7-10 ship here).

**`/execute-plan` (audit port #7) — `skills/execute-plan.md`.** Stop-condition-driven plan walker. Reads `plan.md`, finds the next unimplemented success criterion in §3, and works through it with explicit STOP conditions between steps. Production tier confirms at each step; standard confirms between criteria; sketch flows without auto-stops. The Cutting-phase discipline that prevents "just keep going" agent drift. Pairs with `/mark` (which sets up the failing tests batch) — `/mark` is plan→tests, `/execute-plan` is one-test-at-a-time-cutting.

**`/swarm` (audit port #8) — `skills/swarm.md`.** The biggest port. Subagent-driven development pattern: for plans with multiple independent clusters, dispatches each to a fresh isolated subagent via the Task tool, plus per-cluster auto-review by a SECOND isolated subagent. Two-stage isolation enforced: writer ≠ reviewer, both ≠ orchestrator. Parent session tracks all subagents via TodoWrite. Reviews land in `reviews/cluster-<name>-<sha>.md` with `Engine: swarm-reviewer-subagent` header. **Fully closes audit hole #1** (auto-review on cluster PRs) — PR #22 isolated the reviewer; `/swarm` isolates the implementer too, and bundles per-cluster auto-review into the workflow itself. Refuses to run on sketch tier (ceremony fights iteration); refuses to run if Task tool isn't available (isolation IS the point). 3+ cluster threshold suggested — for 1-2 clusters, use `/execute-plan` instead.

**`/tdd` (audit port #9) — `skills/tdd.md`.** Strict RED-GREEN-REFACTOR cycle, tier-gated. **Joinery's deliberate divergence from obra/superpowers**: upstream makes TDD a universal iron law; Joinery makes it tier-gated because the `sketch` tier exists for comprehension-first exploration where the ceremony fights the work. Mandatory on production (no code without a test observed RED first; paste failure output as `/verify`-style evidence). Recommended on standard (skill surfaces, user can decline). Off by default on sketch (manual invoke only). Distinct from `/mark`: `/mark` is batch plan→tests; `/tdd` is the one-test-at-a-time loop.

**`/writing-skills` + `/receiving-review` (audit port #10) — `skills/writing-skills.md` + `skills/receiving-review.md`.** Two documentation skills.

`/writing-skills`: meta-skill for authoring Joinery skills. TDD-analog 5-step workflow (RED triggers → GREEN procedure → REFACTOR cold-read → DOGFOOD in real project → SHIP after 3 consecutive clean dogfoods). Covers anatomy, naming conventions, the three skill locations (Joinery-built / project-local / user-global), tier discipline. Adapted from obra/superpowers `writing-skills`.

`/receiving-review`: counterpart to `/review`. The discipline for handling review feedback honestly. Load-bearing principle: the writer is the LEAST objective person to evaluate review feedback, so the default response is "the reviewer probably caught something I missed" — not "the reviewer doesn't understand my reasoning." Three response categories ("fix it" / "fair point — record + defer to SQ" / "I disagree — reason is X"), with the disagreement discipline requiring written-down reasoning that would pass another reviewer's evaluation. Tier-gated enforcement via the pre-push hook + `workshop session end` Phase 1 gate (both wired in PR #21).

**`skills/using-joinery.md` updated** to surface all 5 new skills in the meta-skill's available-commands map + trigger-to-skill table. Future session-start orientation will list `/execute-plan`, `/swarm`, `/tdd`, `/writing-skills`, `/receiving-review`.

**Net: audit-driven porting plan is now complete.** 8 PORT verdicts from the audit (3 SKIP, 2 REJECT explicitly preserved). PR #21 surfacing layer + PR #22 isolated subagent review weren't on the original 10-PR audit list but emerged during the porting work — both shipped. The framework now has the full obra/superpowers session-isolation discipline (SessionStart hook, isolated review, isolated implementation, two-stage review, TodoWrite-tracked subagents) without inheriting upstream's slash-command deprecation, plugin-distribution model, or universal-TDD-as-iron-law.

### Fixed — roborev integration corrected against real-world v0.55.0 behavior

Followed up on `workshop setup` shipping with several identifiers that turned out to be wrong. Verified against roborev's actual README + v0.55.0 release notes (2026-05-15) and patched:

**Install paths (workshop setup):**
- **Removed:** Windows `winget install --id roborev.roborev -e` — no such winget package exists.
- **Removed:** Windows `scoop install roborev` — no such scoop bucket exists.
- **Added:** Windows PowerShell install: `powershell -ExecutionPolicy ByPass -c "irm https://roborev.io/install.ps1 | iex"` — roborev's actual official Windows install path per the README.
- **Added:** Universal `go install github.com/roborev-dev/roborev/cmd/roborev@latest` fallback for users with Go 1.25+.
- macOS brew tap (`brew install roborev-dev/tap/roborev`) and Linux curl one-liner are unchanged — these were already correct.

**Per-project init:** `workshop setup` now also runs `roborev init` if invoked from inside a Joinery project (cwd has `.git` + `.workshop`). This installs roborev's own post-commit + post-rewrite hooks in that project, which is what actually enables auto-fire on every commit. Previously the user had to remember this manually.

**Pre-push hook (the critical fix):** the hook was reading `reviews/<sha>.md` files that **roborev never writes** — reviews live in a SQLite DB at `~/.roborev/reviews.db`. The hook would have silently let every push through regardless of findings. Now uses `roborev show <sha> --json | jq -e '...'` to query for unresolved critical/high findings on each commit in the push range, refusing the push if any exist. Graceful degradation: if `roborev` or `jq` isn't installed, the gate is skipped silently (users without roborev don't get spurious push failures).

**Severity vocabulary in `/review` skill:** updated from `Critical / Important / Nits` (Joinery's original spec) to roborev's actual four-tier `critical / high / medium / low`. The fallback path (when roborev isn't installed) still writes `reviews/<sha>.md` markdown files, but uses the same vocabulary for consistency.

**`workshop doctor` enhancements:** when roborev is found, also runs `roborev status` to check daemon health — surfaces "daemon: healthy" / "NOT HEALTHY" / "unable to check" so users catch a dead background daemon before it silently stops reviewing.

Honest note: the pre-push jq filter pattern (`.findings[].severity`, `.status`) is inferred from roborev v0.55.0's documented `--json` output shape. If the JSON schema shifts in a future roborev release, the filter may need adjustment. Field names checked: `severity` falls through to `level` if absent; status normalization handles `resolved`, `dismissed`, `fixed`.

### Added — `workshop setup` installs roborev cross-platform

Closes the friction surfaced during the placket-ops dogfood: the framework adopted roborev as the auto-review engine but had no way to actually install it — users had to know about `brew install roborev-dev/tap/roborev` (which doesn't work on Windows / Linux-without-brew anyway) and remember to run it. That breaks the "unified framework" promise.

`workshop setup` is the one-time global setup command. Detects platform, runs the appropriate install path:

- **macOS:** `brew install roborev-dev/tap/roborev`
- **Linux:** Homebrew on Linux if present
- **Windows:** `winget install --id roborev.roborev -e` → falls back to `scoop install roborev`
- **Universal fallback (any OS):** `bash -c "curl -fsSL https://roborev.io/install.sh | bash"` — requires `bash` and `curl` (Git Bash on Windows works)

Each attempt is tier-aware: prerequisite tool missing → skipped quietly (not an error). Each install has a 300s timeout. On total failure, prints a clear next-step block pointing at the install docs URL and explicitly noting that the framework still works (`/review` falls back to Claude Code built-in); only the auto-fire-on-commit behavior requires roborev specifically.

Idempotent: if `roborev` is already on PATH, the command is a no-op.

Confirmation prompt before installing (skippable with `--yes` for CI / scripted use) — user consent before system-level package installs.

Implementation: new `joinery/setup.py` module + `workshop setup` CLI command. 6 new tests covering the no-op path, platform-specific attempt construction, short-circuit on first success, and the failure-help formatting.

### Changed — `workshop session end` is now a real orchestrator (audit-driven port #5)

Closes the deferred-audit gap #3 — `workshop session end` previously printed framing but did not actually drive the session-close sequence. Now it does, in two coordinated layers:

**CLI side (`workshop session end`)** runs deterministic branch-state checks before handing off to the agent:
- Current branch + commits ahead of `origin/<main>` (configurable via `[git.branching] main_branch`)
- Uncommitted-files check
- Open PR detection via `gh pr list --head <branch>` (gracefully skipped if `gh` unavailable)
- Tier surfaced explicitly

The output is a state snapshot the agent can read at session-end time without re-running git itself.

**Skill side (`/workshop-session-end`)** now drives 7 phases:
1. **Verify tests pass** (hard gate — red = stop, don't proceed)
2. **Detect branch state** (reads what the CLI surfaced)
3. **Present the branch-finishing menu** — context-appropriate options depending on whether you're on main vs a feature branch, ahead of main, with/without an open PR
4. **Execute the chosen path** — with a **production-tier `/review` gate before any merge**: no merge without a `reviews/<sha>.md` for the latest commit. Closes part of gap #1 (auto-review).
5. **Comprehension gate** via `/explain-back`
6. **`/handover` overwrites HANDOVER.md**
7. **Side-quest reconciliation + primary/secondary ratio + token report**

Pattern (verify → detect-environment → menu → execute) ported from obra/superpowers v5.1.0 `finishing-a-development-branch`. Joinery's version adds comprehension + handover + learning layers on top — upstream stops at branch-finishing, Joinery treats the session as the larger unit.

The `/review` gate in Phase 4 means production-tier merges automatically get adversarial review unless the user explicitly opts out — fixing the "we shipped 5 cluster PRs without a single review running" pattern Ryan hit during the placket-ops dogfood.

### Added — `/verify` skill (audit-driven port #4)

Evidence-before-claims gate. Forces production of concrete evidence — test output, command + output, log excerpt, screenshot, DB query — before any work is declared "done" or "working." Protects against the most common AI-era failure mode: declaring work done because the response sounded coherent, not because the result was confirmed.

Discipline: **a claim is not evidence.** "It should work now" is not "it works now." The skill's output template requires a specific claim, an evidence type, the actual evidence pasted (not summarized — pasted), and a verdict of `verified | partial | failed`.

Pairs with `/debug` (verify the fix) and `/explain-back` (verify before summarizing). Tier-agnostic but most strictly applied in `production`.

Adapted from obra/superpowers v5.1.0 `verification-before-completion`.

### Added — `/debug` skill (audit-driven port #3)

Four-phase systematic debugging: **reproduce → isolate → understand → fix**, with the load-bearing rule "no fix without identified root cause." Each phase has a stop condition before moving to the next, so the discipline holds against the temptation to skip from "I see what's wrong" to "let me try this."

The skill teaches:
- **Phase 1 (Reproduce)** — precise symptom statement + deterministic minimum reproduction. 30-min cap then surface non-determinism honestly.
- **Phase 2 (Isolate)** — bisect, remove suspected causes one at a time, narrow to specific line/branch.
- **Phase 3 (Understand)** — state root cause as one sentence that survives three "but why" questions. Predict what fixing it should change. Verify hypothesis BEFORE writing the fix.
- **Phase 4 (Fix)** — failing test first, fix the root cause not the symptom, verify predicted change happens, grep for siblings with the same shape.

Output template at session end produces a short report (symptom / repro / root cause / fix / siblings checked / test added) suitable for PR descriptions.

Adapted from obra/superpowers v5.1.0 `systematic-debugging`. Tier-agnostic — applies in `production`, `standard`, and `sketch`.

### Added — SessionStart hook + `using-joinery` meta-skill (audit-driven port)

The first port from the obra/superpowers audit (see `docs/audits/obra-superpowers-2026-05-18.md` §4 PR #1). Closes part of the deferred-audit gap and lays the foundation for several downstream ports.

What it does: every time a Claude Code session opens on a Joinery project — at startup, after `/clear`, or after `/compact` — a SessionStart hook fires that auto-injects an orientation block into the session's context. The block contains:

- The project's tier (`production` / `standard` / `sketch`) read from `.workshop/tier.lock`
- Whether `plan.md` is present
- A summary of currently-open side quests (parsed from `learning/side-quests.md`)
- The last session's HANDOVER content (if present)
- The full `using-joinery.md` meta-skill content (rules, available skills, the 5-phase rhythm)

The agent therefore starts every session already oriented — knowing which tier governs, which side quests are open, what skill catalog is available, and what rules to never violate. No more "what is Joinery, what tier am I in, what's the workflow" rediscovery cost per session.

Three new artifacts ship under `workshop init` / `workshop adopt`:

- `joinery/skills/using-joinery.md` — the meta-skill content (mirrored to both `.claude/skills/` and `.claude/commands/`)
- `joinery/templates/session_start_hook.py.template` → installed as `.workshop/hooks/session_start.py` in the target project, runs as a Python script (cross-platform, no shell deps)
- `joinery/templates/claude-settings.json.template` → installed as `.claude/settings.json` in the target project, wires the SessionStart hook config to invoke the script

The hook is fail-safe: if anything inside the script throws, it returns empty `additionalContext` so the session still opens cleanly. No crash path.

Implementation: new `write_session_start_hook()` helper in `init.py`, called from both `scaffold()` and `adopt()`. Two new tests covering hook+settings install and the using-joinery skill landing in both `.claude/` dirs.

Pattern ported from obra/superpowers v5.1.0's SessionStart hook + `using-superpowers` meta-skill. Joinery's version reads project-local state (tier, side quests, HANDOVER) which the upstream doesn't, because Joinery is project-local-by-design.

### Changed — `install_skills` writes to both `.claude/skills/` AND `.claude/commands/`

Joinery scaffolds the 23 skill files into a Claude Code project. Before this change they landed only in `.claude/skills/` — which matches Claude Code's user-global skills convention (`~/.claude/skills/`) but does NOT make them invokable as project-local slash commands. Users running `/mark`, `/plan`, `/sq` got "Unknown command" errors because Claude Code's project-local slash commands live in `.claude/commands/`.

`install_skills` now writes the same 23 files to **both** locations. Same content, two paths, both invocation styles work:

- `.claude/skills/` — auto-discovery (where Claude Code's skill system looks)
- `.claude/commands/` — explicit `/<skill-name>` invocation

`workshop adopt` benefits the same way (it calls `install_skills` too). New init/adopt projects get clean slash-command access out of the box; existing projects can re-run `workshop update` to pick up the second location.

Two new tests: `test_scaffold_installs_skills_to_both_locations` (verifies parity between the two dirs) and `test_scaffold_version_string_matches_package` (catches a future regression where the managed-by marker drifts from the package version).

### Fixed — `pyproject.toml` version bumped to 0.1.6

The version string in `pyproject.toml` and `src/joinery/__init__.py` was stuck at `0.1.0` despite multiple feature releases shipping (workshop adopt, answers file, safety scan, dry-run, transaction log, rollback, diff/update, gitignore scaffold, pre-push bootstrap fix, skills→commands location fix). Bumped to `0.1.6` to reflect the actual state. Test for `workshop --version` now reads from `__version__` instead of hardcoding the literal, so future bumps don't silently regress.

### Fixed — pre-push hook blocked the bootstrap push of `main`

The production-tier `pre-push` hook refused every push that touched `refs/heads/main`, including the very first push that *creates* the branch on the remote. New projects couldn't ship their initial commit without bypassing the hook, defeating the framework's branching discipline before it even started.

- The hook now distinguishes `remote_sha == 0…0` (ref doesn't exist on remote yet — bootstrap) from a real update sha. Bootstrap pushes pass; updates to an existing remote main still get refused, exactly as designed.
- The hook also trims a potential trailing `\r` from the SHA so CRLF-formatted stdin (Windows git, some refspecs) doesn't poison the equality check.
- 3 new tests under `tests/test_hooks_pre_push.py` exercising bootstrap creation, main-update refusal, and feature-branch passthrough. Skipped automatically when `bash` is unavailable.

### Added — scaffolded `.gitignore`

`workshop init` and `workshop adopt` now write a language-appropriate `.gitignore` at the project root. Previously neither command scaffolded one, leaving fresh projects with `.joinery/` audit state and `.env` files visible to `git status` and at risk of being committed.

- New templates under `templates/gitignore/`: `.gitignore.python`, `.gitignore.typescript`, `.gitignore.polyglot`. Each includes language-specific build artifacts, virtualenvs/`node_modules/`, tooling caches, editor/OS noise, secrets (`.env`, `*.pem`, `*.key`), and Joinery's own local-only paths (`.joinery/`, `.workshop/usage.jsonl`).
- New helper `templates.select_gitignore_template(language)` mirroring `select_config_template(tier)`.
- New helper `init.write_gitignore(target, language, ctx, ...)` used by both `scaffold()` (init) and `adopt()`. Under adopt, `skip_existing=True` preserves any pre-existing `.gitignore` so user customisations are not clobbered.
- `.gitignore` is recorded in `.workshop/answers.toml` as a managed file (so future `workshop diff` flows can detect drift).
- 6 new tests: gitignore presence + language-specific contents + manifest tracking + adopt preserves vs writes.

### Added — `workshop adopt`

Mid-project adoption command for installing the framework into an existing codebase. Where `init` requires an empty target and scaffolds a fresh project, `adopt` overlays Joinery onto whatever is already there:

- `workshop adopt [--tier T] [--lang L] [--path P] [--force] [--no-hooks]` — runs in the current directory by default
- **Non-destructive by default.** Existing files (`README.md`, prior `CLAUDE.md`, etc.) are preserved and reported, not overwritten. `--force` opts into overwriting framework files.
- **Refuses re-adoption.** If `.workshop/tier.lock` already exists, the command exits with a clear error message unless `--force` is passed.
- **Does not auto-commit.** Files are written to the working tree; the user reviews the diff and stages them through their normal git workflow.
- **Handles non-git targets.** Adopts framework files but skips hook installation, with a printed note explaining how to install hooks after `git init`.
- Project name is derived from the target directory's name; language auto-detected from existing files (Python / TypeScript / polyglot) with a fallback to `polyglot` when nothing matches.

### Changed — `init.py` refactor (internal)

`scaffold()` now composes six module-level helpers (`write_project_files`, `write_learning_module`, `write_tier_adr`, `write_workshop_state`, `install_skills`, `install_hooks_into`) instead of inlining the file-laying logic. The same helpers back `adopt()` with `skip_existing=True`. Public API unchanged — `scaffold()` signature and return type are identical. `copy_template` and `copy_tree` in `templates.py` gain an optional `skip_existing=False` keyword for the same purpose.

### Added — answer file `.workshop/answers.toml`

Every `workshop init` and `workshop adopt` now writes a tracked answer file recording what Joinery installed in the project. This is the foundation for future `workshop diff` / `workshop update` / `workshop migrate` flows — without it, Joinery has no durable memory of which files in your repo it manages.

The file is plain TOML:

```toml
joinery_version = "0.1.x"
mode = "adopt"          # or "init"
tier = "production"
language = "python"
project_name = "my-app"
created_at = "2026-05-11T..."

[files]
managed = ["CLAUDE.md", "plan.md", ...]
preserved = ["README.md", ...]  # adopt only — files Joinery skipped

[hooks]
installed = ["pre-commit", "pre-push", ...]
preserved = []
```

New module: `src/joinery/manifest.py` with `Manifest` dataclass + `read_manifest()` / `write_manifest()`. Hand-written TOML serializer (the schema is small and fixed) — no new dependencies. Stdlib `tomllib` for reads (Python 3.11+).

### Added — `managed-by` markers in rendered templates

Files Joinery writes now carry a `<!-- managed-by: joinery@VERSION -->` HTML comment at the top (hidden in rendered markdown). Applied to CLAUDE.md, plan.md, AGENTS.md, HANDOVER.md, README.md, the learning module, and the tier-selection ADR. The marker is informational for v0.1.x; future update flows will use it together with the answer file to distinguish framework-managed files from user-edited ones.

### Added — pre-adopt safety scan + hook backup

`workshop adopt` now runs a safety scan before writing anything. The scan inspects the target for conditions that make adoption risky:

- **Dirty working tree** — refuses adoption (ERROR) so the resulting diff is reviewable. Bypass with `--allow-dirty`.
- **Sensitive paths** like `.env`, `.env.*`, `*.pem`, `*.key`, `credentials.json`, `.aws/`, `.ssh/`, `secrets/`, `id_rsa`, `id_ed25519` — surfaces them as warnings so the user knows what Joinery's new hooks might encounter.
- **Alternative hook managers** like husky, lefthook, the pre-commit framework — warns that Joinery's hooks may chain awkwardly with theirs.
- **Existing git hooks** — notes that they will be backed up to `.joinery/backup/hooks-<timestamp>/` before Joinery installs its own.

The scan is run in addition to existing checks (empty target, already-adopted). Errors halt adoption unless overridden; warnings/info are surfaced in the summary but do not block. New CLI flags:

- `--allow-dirty` — bypass the dirty-tree check
- `--no-scan` — skip the entire scan (escape hatch for CI / recovery)

Hook backup is always non-destructive. Existing non-`.sample` files in `.git/hooks/` are copied to `.joinery/backup/hooks-YYYYMMDDTHHMMSSZ/` before Joinery installs its own. The backup path is returned in `AdoptResult.hooks_backup` and printed in the adoption summary.

New module `src/joinery/preadopt.py` with `PreAdoptReport` dataclass, `UnsafeAdoptError`, `scan()`, and `backup_hooks()`. 16 new unit tests in `tests/test_preadopt.py`; 5 new integration tests in `tests/test_adopt.py` covering dirty-tree refusal, `--allow-dirty` bypass, `--no-scan` bypass, hook backup, and sensitive-path warnings.

### Added — `--dry-run` flag + transaction log + `workshop rollback`

Three changes that together give Joinery a full preview/audit/undo loop on top of `init` and `adopt`:

- **`--dry-run` on `init` and `adopt`** — previews exactly what would be written without touching the filesystem. The pre-adopt safety scan still runs (read-only). The return value reflects what would have happened so callers can show a diff. No git operations, no manifest write, no transaction log, no hook backup.
- **Transaction log at `.joinery/transactions/<timestamp>.json`** — every real (non-dry-run) `init` or `adopt` appends a JSON record listing every file written, every file preserved, every hook installed, and the path to any hook backup. Append-only audit trail; Joinery never modifies an existing transaction.
- **`workshop rollback`** — undoes the most recent transaction. Deletes every file the transaction wrote (unless `--keep-files`), restores hooks from the recorded backup, and removes the transaction record. Bounded to the most recent operation — for older history, use git.

New modules:
- `src/joinery/transactions.py` — `Transaction` dataclass, `write_transaction()`, `read_transaction()`, `list_transactions()`, `latest_transaction()`. JSON storage (stdlib `json`, no new deps).
- `src/joinery/rollback.py` — `rollback()` function + `NoTransactionError`. Restores hooks via `shutil.copy2` from the backup directory captured in the transaction.

New tests: 9 in `tests/test_transactions.py` (round-trip, chronological listing, invalid-mode rejection); 7 in `tests/test_rollback.py` (init + adopt rollback, hook restore, user-file preservation, --keep-files, graceful handling of already-deleted files); 5 in `tests/test_adopt.py` and `tests/test_init.py` combined (dry-run produces no writes, transaction log written on real runs).

CLI changes:
- `workshop init` and `workshop adopt`: new `--dry-run` flag.
- `workshop rollback` (new subcommand): `--path P`, `--keep-files`, `--yes` (skip confirmation).
- Adoption summary now uses "Would write" / "Would preserve" verbs under `--dry-run` and prints "Dry run complete — re-run without --dry-run to apply."

### Added — `workshop diff` + `workshop update`

The payoff for the answer-file foundation: Joinery can now detect and apply drift between a project's managed files and the framework's current templates.

- **`workshop diff`** — read-only. For every rendered file Joinery manages (CLAUDE.md, plan.md, AGENTS.md, HANDOVER.md, README.md, learning/, ADR, `.workshop/config.toml`), compares the on-disk content against what the current templates would produce. Prints per-file status (clean / drifted / missing) and a unified diff per drifted file. Also surfaces `joinery_version` bumps (manifest version → current).
- **`workshop update`** — apply pending drift. Walks the diff, writes the freshly-rendered template content for each drifted or missing file, refreshes `.workshop/answers.toml` to record the current Joinery version, and appends a new transaction log entry. Supports `--dry-run`, `--yes`, and `--path`.

**Stable diff context.** Time-based template variables (`init_at`, `date`, `last_session_end`, `week`) are pinned to the manifest's `created_at` during diff, so the report shows real drift (template content changes, version bumps) rather than noise from clock movement. To make this work, `init` and `adopt` now both pass `ctx["init_at"]` as the manifest's `created_at` so the value rendered into the project's files matches the value the diff reads back.

**Scope.** Drift detection covers RENDERED files only. Non-rendered managed files (hooks, skills, `.workshop/usage.jsonl`, `.workshop/tier.lock`, `.workshop/answers.toml`) are excluded — they don't carry template content. Preserved (user-owned) files are never touched.

New modules:
- `src/joinery/diff.py` — `DiffReport`, `FileDiff`, `diff_managed_files()`, `render_managed_state()`, `NotAdoptedError`. Uses stdlib `difflib.unified_diff`.
- `src/joinery/update.py` — `UpdateResult`, `apply_updates()`. Writes managed-file updates, refreshes the manifest, appends a transaction.
- `src/joinery/templates.py`: new public helper `render_template_file()` for diff/update flows that need rendered content without filesystem writes.

CLI changes:
- `workshop diff [--path P]` — new read-only subcommand.
- `workshop update [--path P] [--dry-run] [--yes]` — new subcommand. Confirms before writing unless `--yes`.

New tests: 7 in `tests/test_diff.py` (clean state, user edit detection, missing file, non-rendered file exclusion, stable time context, render_managed_state coverage), 9 in `tests/test_update.py` (no-op, drift application, missing-file restoration, dry-run, transaction recorded, manifest version refresh, --only filter, diff-update round-trip).

Internal: `transactions.write_transaction()` now uses microsecond-precision timestamps in filenames so two transactions in the same second (e.g., init then update) produce distinct files.

### Tests

18 new tests in `tests/test_adopt.py` (adopt), 8 in `tests/test_manifest.py` (round-trip + edge cases), 16 in `tests/test_preadopt.py` (safety scan + backup), 9 in `tests/test_transactions.py` (audit log), 7 in `tests/test_rollback.py` (undo flow), 7 in `tests/test_diff.py` (drift detection), 9 in `tests/test_update.py` (apply drift), and 3 additions each to `test_init.py` and `test_adopt.py` covering answer-file content + marker presence. Full suite now 133 passing (was 42 at v0.1.0).

## [0.1.0] — 2026-05-10

First pre-alpha release. The complete v1 framework: templates, skills, hooks, and the workshop CLI. Built from a 2000-line design specification and dogfooded on itself (production-tier discipline applied from the first commit).

### Added — workshop CLI

Python click-based command-line tool, installable via `pip install -e .` (or `pipx install joinery-cli` once published).

- `workshop init <name>` — scaffold a new project (interactive or flag-driven). Reads tier-variant templates, renders Jinja2 placeholders, installs hooks, copies skills, initializes git, makes initial commit.
- `workshop session start` — reads HANDOVER, runs preflight (git status, plan freshness on production), prints session-start summary.
- `workshop session end` — frames the session-end ritual; agent-driven steps via `workshop-session-end` skill.
- `workshop promote <project> --to <tier>` — additive scaffold upgrade (sketch → standard → production). Refuses demotion.
- `workshop doctor` — verifies workshop + project health (config, hooks, sync state, plan freshness).

Modules in `src/joinery/`: cli, init, session, promote, doctor, lang, config, templates, git, paths. Dependencies: click, jinja2. Python 3.11+.

42 pytest tests passing. mypy --strict clean. ruff check + format clean.

### Added — 23 skills

Composable markdown skill files in `skills/`. Auto-invoke from natural language for most; manual-only for `rule`, `audit`, `security-review` where intentionality matters; hook-fired or composed for the rest.

- Planning (6): `plan` (orchestrator, leverages Claude Code plan mode), `plan-system`, `plan-data`, `plan-flows`, `plan-decisions`, `plan-side-quests`
- Workflow (7): `mark`, `explain-back`, `handover`, `review`, `security-review`, `adr`, `pr`
- Discipline (4): `rule`, `sq`, `audit`, `digest`
- Documentation (4): `docs`, `docs-changelog`, `docs-getting-started`, `docs-architecture`
- Session (2): `workshop-session-start`, `workshop-session-end`

Audit-first applied — `/review` and `/security-review` adopt Claude Code's built-in skills as the priority path (engine order: roborev > Claude Code built-in > Claude subprocess fallback).

### Added — 4 git hooks

Bash scripts in `hooks/` that `workshop init` installs into `.git/hooks/` of scaffolded projects.

- `pre-commit` — lint + type-check on staged files + AGENTS.md mirror from CLAUDE.md
- `pre-push` — refuses direct main pushes on production; reads `reviews/` for critical findings
- `commit-msg` — Lore Protocol structure on production-tier commits over threshold; bot author bypass
- `post-merge` — preflight refresh + quick lint surface

Each hook under 50 lines of code. `set -euo pipefail` everywhere. Tier-aware via `.workshop/config.toml`. The 5th hook (post-commit, adversarial review) is managed by [roborev](https://github.com/roborev-dev/roborev) when installed.

### Added — 15 project templates

Static markdown and TOML templates in `templates/` with Jinja2 `{{var}}` placeholders, rendered by `workshop init` against project-specific values.

- Project-level: `CLAUDE.md.starter` (5-rule starter), `plan.md.template`, `HANDOVER.md.template`, `README.md.template`, `AGENTS.md.template`
- Workshop-level: `CLAUDE.md.global` (10 default rules)
- Tier configs: `framework.config.toml.production`, `.standard`, `.sketch` (reflecting spec §14 defaults)
- Learning module: side-quests, skills-log, comprehension-audits, ratio-log (empty), weekly-digest
- Tier-selection ADR: `0001-tier-selection.md.template`

### Added — design + documentation

- Full design specification at `docs/spec.md` (~2000 lines, 18 sections)
- 1-page architecture summary at `docs/architecture.md`
- First ADR: tiers as risk profiles, not project categories
- 5-rule starter `CLAUDE.md` (production tier)
- Dogfooded `plan.md` (Joinery's own build plan)
- Minimal OSS hygiene: CONTRIBUTING, SECURITY
- `.gitattributes` for cross-platform LF normalization

### Known limitations

- `workshop setup` not yet implemented (the doctor reports `~/.config/joinery/ MISSING` and tells you to run setup; the command lands when first needed)
- External sync adapter pattern is spec'd but no skeleton ships yet
- No GitHub Actions CI workflow; lint + typecheck + tests run locally only
- Cross-platform CI testing deferred — Windows verified, Linux relies on pure stdlib + click + jinja2 portability
- Deeper audit of `obra/superpowers` deferred to first real dogfood
