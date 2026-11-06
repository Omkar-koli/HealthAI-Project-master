# Enabled APIs that are part of HealthAI's architecture. The project also has
# ~27 other APIs enabled (BigQuery and its sub-APIs, Dataform, Dataplex, DNS,
# Domains, Filestore, Pub/Sub, etc.) that are unrelated to this app and are
# listed as an exception in the written analysis, not managed here.
locals {
  core_apis = [
    "compute.googleapis.com",
    "container.googleapis.com",
    "artifactregistry.googleapis.com",
    "sql-component.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "servicenetworking.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ]
}

resource "google_project_service" "core" {
  for_each = toset(local.core_apis)

  project = var.project_id
  service = each.value

  # Don't let "terraform destroy" accidentally disable an API the whole
  # project depends on just because it's being removed from this list.
  disable_on_destroy = false
}

import {
  for_each = toset(local.core_apis)
  to       = google_project_service.core[each.value]
  id       = "healthai-508921/${each.value}"
}
