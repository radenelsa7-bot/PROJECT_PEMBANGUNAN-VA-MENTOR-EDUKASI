# ERD VAME (Virtual Assistant Mentor Edukasi)

Skema relasional menurut SRS Appendix B.2.

```mermaid
erDiagram
    USER ||--o{ ENROLLMENT : has
    USER ||--o{ STATE_TRANSITION_LOG : generates
    USER ||--o{ EVALUATION_ATTEMPT : creates

    CURRICULUM ||--o{ MODULE : contains
    CURRICULUM ||--o{ ENROLLMENT : enrolls

    MODULE ||--o{ READING_POINT : has

    READING_POINT ||--o{ QUESTION : has
    READING_POINT ||--o{ LEARNING_PROGRESS : tracked
    READING_POINT ||--o{ SESSION : relates

    ENROLLMENT ||--o{ SESSION : owns
    ENROLLMENT ||--o{ LEARNING_PROGRESS : tracks

    SESSION ||--o{ MESSAGE : contains
    SESSION ||--|| EVALUATION : produces

    EVALUATION ||--o{ ANSWER : includes

    QUESTION ||--o{ EVALUATION_ATTEMPT : attempts

    USER {
        int id PK
        string name
        string email UK
        string password_hash
        string role "learner | admin"
        datetime created_at
    }

    CURRICULUM {
        int id PK
        string code UK
        string title
        string short_name
        string description
        string level
        string topic_label
        int est_hours
        string mentor_name
        bool is_active
    }

    MODULE {
        int id PK
        int curriculum_id FK
        string title
        string label
        int order
    }

    READING_POINT {
        int id PK
        int module_id FK
        string title
        text content
        string objective
        string keywords_json
        string references
        int order
        bool is_mandatory
    }

    ENROLLMENT {
        int id PK
        int user_id FK
        int curriculum_id FK
        string status "active | completed | dropped"
        float progress_persen
        datetime started_at
        datetime completed_at
    }

    LEARNING_PROGRESS {
        int id PK
        int user_id FK
        int reading_point_id FK
        string status "LOCKED | ACTIVE | COMPLETED"
        float best_score
        datetime updated_at
    }

    STATE_TRANSITION_LOG {
        int id PK
        int user_id FK
        int reading_point_id FK
        string from_status
        string trigger
        string to_status
        bool valid
        string note
        datetime created_at
    }

    SESSION {
        int id PK
        int enrollment_id FK
        int reading_point_id FK
        string status "active | ended"
        datetime started_at
        datetime ended_at
    }

    MESSAGE {
        int id PK
        int session_id FK
        string role "user | mentor"
        text content
        string kind "normal | out_of_scope | blocked"
        bool flagged
        string flag_reason
        datetime created_at
    }

    EVALUATION {
        int id PK
        int session_id FK
        float score
        bool is_passed
        text feedback_ai
        datetime evaluated_at
    }

    ANSWER {
        int id PK
        int evaluation_id FK
        int question_id FK
        text answer_text
        float score_awarded
        text feedback
    }

    QUESTION {
        int id PK
        int reading_point_id FK
        text question_text
        text answer_key
        string question_type "essay | multiple_choice"
        int weight
        string difficulty
        datetime created_at
    }

    EVALUATION_ATTEMPT {
        int id PK
        int user_id FK
        int reading_point_id FK
        text question
        text answer
        float score
        text feedback
        bool passed
        string status "pending | graded"
        datetime created_at
        datetime graded_at
    }
```

## 7 status belajar (state machine)

`LOCKED` → `ACTIVE` → `COMPLETED` (semua di `learning_progress.status`). Transisi tidak valid dicatat di `state_transition_logs` (`valid = false`).

## Repositori terkait

- `backend/app/models.py` — definisi SQLAlchemy
- `backend/app/database.py` — session & engine
- `backend/app/seed_data.py` — seed 3 kurikulum, 14 poin Python
