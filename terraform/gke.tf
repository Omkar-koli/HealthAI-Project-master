# GKE Autopilot cluster (Milestone 5). Deliberately minimal on the first pass —
# this resource has dozens of nested settings blocks, so we're letting
# "terraform plan" tell us exactly what's missing rather than guessing them
# all up front, the same way we handled Cloud SQL.
#
# Kubernetes workloads, Ingress, and the managed certificate (everything in
# k8s/) are NOT managed here — those are deployed by the pipeline, per the
# Terraform scope table.
resource "google_container_cluster" "healthai" {
  project  = var.project_id
  name     = "healthai-cluster"
  location = var.region

  enable_autopilot = true
}

import {
  to = google_container_cluster.healthai
  id = "projects/healthai-508921/locations/us-central1/clusters/healthai-cluster"
}
