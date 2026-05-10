---
name: docs-getting-started
description: |
  Refresh docs/getting-started.md from the current project state. Reads pyproject.toml or package.json, scripts, install steps, and produces an onboarding doc that actually works on the current codebase. Triggers when user says "update getting started", "refresh onboarding docs", "the install steps are wrong", "rewrite getting started".
---

# /docs-getting-started — refresh the onboarding doc

## When to use

Manually invokable when the install/run process changes. Auto-suggested by `/docs` orchestrator when this file is detected as stale.

Triggers:
- "update getting started" / "refresh onboarding docs"
- "the install steps are wrong"
- "rewrite getting started"
- Composed by `/docs` when stale

## Procedure

1. **Read project metadata** to understand what kind of project this is:
   - `pyproject.toml` — Python project; read dependencies, scripts, entry points
   - `package.json` — Node/TS project; read scripts, dependencies, engines
   - `Dockerfile`, `docker-compose.yml` — containerized; note that
   - `Makefile` or `justfile` — task runner; read targets

2. **Read the README.md** for the project description and any existing setup notes.

3. **Identify the actual install + run sequence** by reading the relevant scripts:
   - For Python: `pip install -e .` typically; with `[dev]` extras if dev tools needed
   - For Node/TS: `npm install` or `pnpm install` etc., then a run script
   - For Docker: build image, run container

4. **Test the sequence mentally.** Walk through each step as a fresh contributor. What's missing? Common gaps:
   - Required environment variables
   - Required external services (database, etc.)
   - Required tool versions (Python 3.11+, Node 20+)
   - Authentication setup

5. **Compose `docs/getting-started.md`:**

   ```markdown
   # Getting Started

   <One paragraph: what this project is for, who this doc is for.>

   ## Prerequisites

   - <Tool> >= <version>
   - <External service> running (or stub instructions)

   ## Install

   ```
   <step-by-step shell commands>
   ```

   ## Run

   ```
   <how to start the dev server / CLI / app>
   ```

   ## Test

   ```
   <how to run the test suite>
   ```

   ## Common issues

   - <issue 1>: <fix>
   - <issue 2>: <fix>

   ## Where to go next

   - `docs/architecture.md` — system design overview
   - `plan.md` — current plan
   - `CONTRIBUTING.md` — contribution guidelines (if applicable)
   ```

6. **Verify steps are real.** Don't write `npm run dev` if `package.json` doesn't have a `dev` script. Read the actual config and write what's actually there.

7. **Commit:**
   ```
   docs: refresh getting-started after install changes
   ```

## Output format

Updated `docs/getting-started.md`.

## Notes

- The honest test: a stranger runs through this doc top to bottom, on a fresh machine, and gets to a running project. If they hit a wall, the doc is incomplete.
- "Common issues" section is empty at first — populate over time as real onboarding friction surfaces.
- Don't fabricate prerequisites. Read the actual config; write what's actually required.
