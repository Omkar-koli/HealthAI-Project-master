-- 001_create_studies.sql
-- Baseline schema for HealthAI. Applied by a human/CI, NOT by the application.
-- (Before Milestone 4 the app created this table at startup with SQLAlchemy's
--  create_all(); that code has been removed so schema changes are explicit.)
--
-- Apply with:
--   psql -h <host> -U <admin_user> -d healthai -v ON_ERROR_STOP=1 -f migrations/001_create_studies.sql

BEGIN;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(64) PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE studies (
    id                   SERIAL        NOT NULL,
    patient_name         VARCHAR(255),
    image_name           VARCHAR(255)  NOT NULL,
    image_path           VARCHAR(500)  NOT NULL,   -- object name in the uploads bucket (e.g. uploads/Jane_ab12cd34.png)
    status               VARCHAR(32)   NOT NULL,
    predicted_condition  VARCHAR(128),
    confidence           FLOAT,
    prediction_results   JSON,
    created_at           TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id)
);

CREATE INDEX ix_studies_id ON studies (id);

INSERT INTO schema_migrations (version) VALUES ('001_create_studies');

COMMIT;
