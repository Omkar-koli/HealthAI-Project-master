# Uploads bucket (Milestone 4). Imported, not newly created — see import block below.
resource "google_storage_bucket" "uploads" {
  name                        = "healthai-uploads-508921"
  project                     = var.project_id
  location                    = "US-CENTRAL1"
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  public_access_prevention = "enforced"
}

import {
  to = google_storage_bucket.uploads
  id = "healthai-uploads-508921"
}
