\echo '--- applied migrations'
SELECT version, applied_at FROM schema_migrations ORDER BY version;
\echo '--- row count (NEW database)'
SELECT COUNT(*) AS new_row_count FROM studies;
\echo '--- role attributes'
SELECT rolname, rolsuper, rolcreaterole, rolcreatedb FROM pg_roles WHERE rolname IN ('postgres','healthai_app') ORDER BY 1;
\echo '--- roles healthai_app belongs to (no rows = not a cloudsqlsuperuser)'
SELECT g.rolname AS member_of
  FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.member JOIN pg_roles g ON g.oid = m.roleid
 WHERE r.rolname = 'healthai_app';
