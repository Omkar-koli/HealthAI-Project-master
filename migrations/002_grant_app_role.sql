-- 002_grant_app_role.sql
-- Least-privilege access for the application's database user.
-- The app user (healthai_app) may read/write rows but can NOT create, alter, or drop tables.
-- The DO block makes this a no-op on a local dev database where that role does not exist.

BEGIN;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'healthai_app') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE studies TO healthai_app;
        GRANT USAGE, SELECT, UPDATE ON SEQUENCE studies_id_seq TO healthai_app;
    END IF;
END
$$;

INSERT INTO schema_migrations (version) VALUES ('002_grant_app_role');

COMMIT;
