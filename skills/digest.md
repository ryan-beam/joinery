---
name: digest
description: |
  Generate the weekly digest. Aggregates side quests counts, skills logged, comprehension audit, primary/secondary ratio, token usage by phase, sessions across projects. Flags audit lapses and stale docs with banners. Triggers when user says "weekly digest", "how was my week", "/digest", or auto-fires Sundays per [learning] digest_day.
---

# /digest — weekly digest

## When to use

Auto-fires on the configured `digest_day` (default Sunday). Manually invokable any time.

Triggers:
- "weekly digest" / "how was my week" / "what got done this week"
- "/digest"
- Auto-fires per `[learning] digest_day` in config

## Procedure

1. **Compute the week range.** Default: last 7 days ending today (or ending on the next `digest_day` if invoked early).

2. **Aggregate side quests:**
   - Count new entries created this week (from `learning/side-quests.md` parse)
   - Count closures this week (status `done` with date in range)
   - Count still-open
   - Identify the oldest still-open SQ ("Hottest open")

3. **Aggregate skills logged:** read `learning/skills-log.md` and list entries with date in range.

4. **Comprehension audit status:**
   - Did `/audit` run this week?
   - If not, compute commits-since-last-audit and days-since-last-audit
   - Compare against `[learning] audit_trigger` thresholds
   - Set audit banner: NORMAL / OVERDUE / LAPSE

5. **Primary/secondary ratio:** read `learning/ratio-log.jsonl`, filter entries in week range, compute primary % and secondary %. Compare against `[learning] ratio_target` (default 30% primary minimum, 70% secondary maximum). Status: HEALTHY / WARNING / DEBT.

6. **Token usage by phase:** read `.workshop/usage.jsonl`, filter to week range, group by phase tag (drafting, marking, cutting, finishing, review). Compute percentages and trend vs prior week.

7. **Sessions:** count sessions across projects this week. Each `workshop session start` is one session.

8. **Docs staleness check:** read mtime of `docs/architecture.md` and `docs/getting-started.md`. If older than `[docs] stale_threshold_days` AND the codebase has shipped commits since, flag with `**DOCS STALE — ...**` banner.

9. **Auto-run `/docs-changelog`** if `[docs] auto_changelog_in_digest = true` (default true). Updates `docs/changelog.md` with this week's commits.

10. **Compose the digest** at `learning/weekly-digests/<YYYY-WNN>.md`:

    ```markdown
    # Workshop Weekly — <YYYY-WNN> (<date range>)

    <Banner section if any flags>

    ## Side quests
    - <N> new this week, <M> closed, <K> still open
    - Hottest open: SQ-NNN (<days> days)
    - Closed this week: SQ-NNN, SQ-NNN

    ## Skills logged
    - YYYY-MM-DD — <concept>
    - YYYY-MM-DD — <concept>

    ## Comprehension audit
    - <status: ran with score N/5 | not run, N commits since last>

    ## Primary/Secondary ratio
    - <N>% primary / <M>% secondary (target: 70% secondary max)
    - <HEALTHY | WARNING | DEBT>

    ## Token usage
    - Total: <count>
    - By phase: planning <N>%, marking <M>%, cutting <K>%, finishing <L>%, review <J>%
    - Trend: <+/-N>% vs last week

    ## Sessions
    - <N> sessions across <project list with counts>
    ```

11. **Banners** at the top if any of:
    - **AUDIT OVERDUE — N commits / D days since last** (past trigger, under 2x)
    - **AUDIT LAPSE — comprehension debt accumulating** (2x past trigger)
    - **DOCS STALE — architecture.md last updated D days ago, codebase has shipped C commits since**
    - **RATIO ALERT — secondary work exceeded 70%**

12. **External sync** — if `[external_sync] enabled = true`, invoke the configured adapter script with the digest content as input.

## Output format

- A new file `learning/weekly-digests/<YYYY-WNN>.md`
- Updates to `docs/changelog.md` (via auto-`/docs-changelog`)
- Optional: external sync call if configured

## Notes

- Token cost ~1-2K. Cheap.
- Banners exist to make discipline atrophy loud. Don't suppress them.
- If digest finds nothing for a section (no SQs closed, no skills logged), say so explicitly — empty sections are a signal.
- The digest is read-only on user data. It doesn't close SQs or modify state beyond writing its own file.
