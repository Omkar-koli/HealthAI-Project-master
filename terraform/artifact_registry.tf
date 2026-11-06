# Artifact Registry repo holding the backend/frontend images (Milestone 3). Imported.
resource "google_artifact_registry_repository" "healthai_repo" {
  project                = var.project_id
  location               = var.region
  repository_id          = "healthai-repo"
  format                 = "DOCKER"
  cleanup_policy_dry_run = true

  docker_config {
    immutable_tags = false
  }
}

import {
  to = google_artifact_registry_repository.healthai_repo
  id = "projects/healthai-508921/locations/us-central1/repositories/healthai-repo"
}
