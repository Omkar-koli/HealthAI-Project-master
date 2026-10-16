# Source this on the VM:   source scripts/cloudsql/env.sh
# Gives you two helpers:
#   load_secrets   - reads both DB passwords from Secret Manager (using the VM's service account)
#                    into THIS shell's memory only. Nothing is written to disk.
#   psqlc <user> [psql args]  - runs psql against Cloud SQL (private IP) from a throwaway postgres container
#                    e.g.  psqlc postgres -c "SELECT 1;"      psqlc healthai_app -c "SELECT 1;"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DB_HOST="${DB_HOST:-10.100.192.3}"
DB_NAME="${DB_NAME:-healthai}"
PG_IMAGE="${PG_IMAGE:-postgres:15-alpine}"

load_secrets() {
  ADMIN_PW="$(gcloud secrets versions access latest --secret=healthai-db-admin-password)" || return 1
  APP_PW="$(gcloud secrets versions access latest --secret=healthai-db-app-password)" || return 1
  export ADMIN_PW APP_PW
  echo "secrets loaded into this shell (admin: ${#ADMIN_PW} chars, app: ${#APP_PW} chars)"
}

psqlc() {
  local user="$1"; shift
  local pw="$APP_PW"
  [ "$user" = "postgres" ] && pw="$ADMIN_PW"
  PGPASSWORD="$pw" docker run --rm -i -e PGPASSWORD -e APP_PW -v "$REPO_DIR:/repo:ro" "$PG_IMAGE" \
    psql -h "$DB_HOST" -U "$user" -d "$DB_NAME" -v ON_ERROR_STOP=1 "$@"
}
