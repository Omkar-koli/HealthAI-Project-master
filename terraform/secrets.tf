# Secret Manager secret CONTAINERS only (Milestone 4). The actual passwords
# are never in Terraform config or state — only the secret resource itself.
resource "google_secret_manager_secret" "db_admin_password" {
  project   = var.project_id
  secret_id = "healthai-db-admin-password"

  replication {
    auto {}
  }
}

import {
  to = google_secret_manager_secret.db_admin_password
  id = "projects/healthai-508921/secrets/healthai-db-admin-password"
}

resource "google_secret_manager_secret" "db_app_password" {
  project   = var.project_id
  secret_id = "healthai-db-app-password"

  replication {
    auto {}
  }
}

import {
  to = google_secret_manager_secret.db_app_password
  id = "projects/healthai-508921/secrets/healthai-db-app-password"
}
