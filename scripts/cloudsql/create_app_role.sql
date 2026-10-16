-- Run once, as the admin user (postgres). Creates the application's database user.
-- The password never appears in this file or on a command line: psql reads it from the
-- APP_PW environment variable, which load_secrets filled from Secret Manager.
-- A role created with SQL does NOT receive cloudsqlsuperuser (unlike one added in the console).
\getenv app_pw APP_PW
SELECT format('CREATE ROLE healthai_app LOGIN PASSWORD %L', :'app_pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'healthai_app') \gexec
SELECT format('ALTER ROLE healthai_app WITH LOGIN PASSWORD %L', :'app_pw') \gexec
