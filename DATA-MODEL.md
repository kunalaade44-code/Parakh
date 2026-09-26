# 🗄️ Database Data Model

```
                    ┌─────────────────────────┐
                    │         EVENTS          │
                    ├─────────────────────────┤
                    │ id (PK)                 │
                    │ name                    │
                    │ submissions_close (UTC) │
                    └────────────┬────────────┘
                                 │ 1..N
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
     ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
     │   TRACKS    │      │  CRITERIA   │      │    TEAMS    │
     ├─────────────┤      ├─────────────┤      ├─────────────┤
     │ id (PK)     │      │ id (PK)     │      │ id (PK)     │
     │ event_id    │      │ name        │      │ name        │
     │ name        │      │ weight      │      │ invite_code │
     └──────┬──────┘      └─────────────┘      └──────┬──────┘
            │                                         │
            │                   ┌─────────────────────┘
            ▼                   ▼
     ┌────────────────────────────────────────────────┐
     │                    PROJECTS                    │
     ├────────────────────────────────────────────────┤
     │ id (PK), team_id, track_id, title, summary,    │
     │ repo_url, demo_url, submitted_at               │
     └──────────────────────────┬─────────────────────┘
                                │ 1..N
                                ▼
     ┌────────────────────────────────────────────────┐
     │                     SCORES                     │
     ├────────────────────────────────────────────────┤
     │ id (PK), judge_id, project_id,                 │
     │ criteria_scores (JSON), comment, submitted_at  │
     └────────────────────────────────────────────────┘
```

## Entity Summary
- **Users**: Central identity records across Organizer, Judge, Participant, and Visitor roles.
- **Sessions**: Ephemeral and pre-seeded auth tokens (`org_7f2a`, `jdg_a_91bc`, `jdg_b_44de`, `prt_2e88`).
- **Events & Tracks**: Hackathon lifecycle definitions with strict deadline constraints.
- **Projects & Scores**: Submissions linked with isolated judge rubric evaluations.
