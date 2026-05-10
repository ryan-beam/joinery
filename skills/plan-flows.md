---
name: plan-flows
description: |
  Produce the Critical flows section of plan.md with Mermaid sequence diagrams for the 2-3 most important user/system journeys. CONDITIONAL — skipped if the system has only one obvious flow. Composed by /plan when non-trivial interactions surface. Triggers with "sequence diagram", "show the flow", "how does X interact with Y", "what's the interaction pattern".
---

# /plan-flows — critical interaction flows

## When to use

CONDITIONAL. Only when the system has non-trivial interactions across components or with external systems. Skip if there's one obvious flow that prose can describe.

Triggers:
- "sequence diagram for X" / "show the flow"
- "how does X interact with Y"
- "what's the interaction pattern between A and B"
- Composed by `/plan` when complex flows surface during planning

## Procedure

1. **Identify the load-bearing flows.** 2-3 maximum. Pick the flows that most influence the design — happy path, primary failure mode, retry/replay logic, etc.

2. **For each flow, identify participants.** User, frontend, API, database, external service, etc. Keep to 4-6 participants per diagram.

3. **Draw the sequence.** Mermaid `sequenceDiagram` syntax. Use `alt` blocks for branches (success vs failure). Use `Note over` sparingly for context that doesn't fit in arrow labels.

4. **Caption each flow.** One-sentence description above each diagram so a reader knows what they're looking at without parsing the syntax.

5. **Surface implications.** If the flow reveals a constraint or design implication (e.g., "this requires idempotency keys"), note it after the diagram.

## Output format

The Critical flows section of `plan.md`:

````markdown
## 7. Critical flows

**Happy path: webhook ingestion.**

```mermaid
sequenceDiagram
  participant E as External
  participant API
  participant Q as Queue
  participant W as Worker
  E->>API: POST /webhooks (event)
  API->>Q: enqueue(event)
  API-->>E: 202 Accepted
  Q->>W: dispatch
  W->>W: process event
```

**Implication:** Workers are async; clients get 202 not 200. They cannot expect immediate processing.

**Replay flow: idempotent retries.**

```mermaid
sequenceDiagram
  participant E as External
  participant API
  participant DB
  E->>API: POST /webhooks (event-id-X)
  API->>DB: SELECT WHERE id = X
  alt Already processed
    DB-->>API: row exists
    API-->>E: 200 (cached result)
  else New event
    DB-->>API: not found
    API->>DB: INSERT (id=X, status=processing)
    API-->>E: 202 Accepted
  end
```

**Implication:** Every webhook event MUST have a stable event-id from the sender.
````

## Notes

- 2-3 flows max. More than 3 is implementation detail — save for actual code.
- Caption matters. A diagram without context is decoration.
- Failure paths matter as much as happy paths. The retry/replay flow often reveals constraints.
