# ---------------------------------------------------------------------------
# Milestone 6, Phase 4: CI/CD pipeline identity. All NEW resources.
#
# The repo restriction is enforced here (attribute_condition below, so only
# Omkar-koli/HealthAI-Project-master can ever use this). The BRANCH
# restriction ("only the deploy branch triggers a release") is enforced in
# the GitHub Actions workflow file itself (on: push: branches: [deploy]),
# not here — that's standard practice for Workload Identity Federation setups.
# ---------------------------------------------------------------------------

resource "google_service_account" "ci_deploy" {
  project      = var.project_id
  account_id   = "healthai-ci-deploy"
  display_name = "HealthAI CI/CD pipeline"
}

# Push built images to Artifact Registry
resource "google_project_iam_member" "ci_deploy_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.ci_deploy.email}"
}

# Deploy to the GKE cluster (kubectl apply, rollout status, rollout undo)
resource "google_project_iam_member" "ci_deploy_container_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.ci_deploy.email}"
}

# Read-only access to the model file in the uploads bucket — scoped to just
# this bucket, not a project-wide storage role, since the same bucket also
# holds patient upload images.
resource "google_storage_bucket_iam_member" "ci_deploy_model_reader" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.ci_deploy.email}"
}

# Workload Identity Pool: the trust relationship with GitHub's OIDC tokens
resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
}

# Provider: GitHub's actual OIDC issuer, restricted to this one repo
resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  # Hard restriction: only workflow runs from this exact repo can use this provider at all.
  attribute_condition = "assertion.repository == \"Omkar-koli/HealthAI-Project-master\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Let GitHub Actions runs from this repo impersonate the pipeline service account
resource "google_service_account_iam_member" "ci_deploy_wif_user" {
  service_account_id = google_service_account.ci_deploy.name
  role                = "roles/iam.workloadIdentityUser"
  member              = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/Omkar-koli/HealthAI-Project-master"
}
