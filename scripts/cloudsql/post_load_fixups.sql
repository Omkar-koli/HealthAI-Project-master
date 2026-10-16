-- Run once, as admin, right after loading the old rows into Cloud SQL.
-- 1) Rows were inserted with explicit ids, so move the sequence past them (otherwise the next insert collides).
SELECT setval('studies_id_seq', (SELECT COALESCE(MAX(id), 1) FROM studies));
-- 2) Old rows point at files on the VM's disk (/app/uploads/x.png); the app now expects bucket object names (uploads/x.png).
UPDATE studies
   SET image_path = 'uploads/' || regexp_replace(image_path, '^.*/', '')
 WHERE image_path NOT LIKE 'uploads/%';
