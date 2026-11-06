# ---------------------------------------------------------------------------
# Service accounts (Milestone 4/5). display_name left unset for now — if the
# real accounts have one set, the next "terraform plan" will show it and we'll
# add it in, the same way we fixed artifact_registry.tf.
# ---------------------------------------------------------------------------

resource "google_service_account" "gke_nodes" {
  project      = var.project_id
  account_id   = "healthai-gke-nodes"
  display_name = "HealthAI GKE nodes"
}

import {
  to = google_service_account.gke_nodes
  id = "projects/healthai-508921/serviceAccounts/healthai-gke-nodes@healthai-508921.iam.gserviceaccount.com"
}

resource "google_service_account" "gke_app" {
  project      = var.project_id
  account_id   = "healthai-gke-app"
  display_name = "HealthAI app (GKE pods)"
}

import {
  to = google_service_account.gke_app
  id = "projects/healthai-508921/serviceAccounts/healthai-gke-app@healthai-508921.iam.gserviceaccount.com"
}

resource "google_service_account" "vm_sa" {
  project      = var.project_id
  account_id   = "healthai-vm-sa"
  display_name = "healthai-vm-sa"
  description  = "Identity for the HealthAI VM"
}

import {
  to = google_service_account.vm_sa
  id = "projects/healthai-508921/serviceAccounts/healthai-vm-sa@healthai-508921.iam.gserviceaccount.com"
}

# ---------------------------------------------------------------------------
# Project-level IAM role bindings (google_project_iam_member import IDs are
# "project_id role member", space-separated).
# ---------------------------------------------------------------------------

# healthai-gke-nodes: Kubernetes Engine Default Node Service Account, Artifact Registry Reader
resource "google_project_iam_member" "gke_nodes_default_node_sa" {
  project = var.project_id
  role    = "roles/container.defaultNodeServiceAccount"
  member  = "serviceAccount:healthai-gke-nodes@healthai-508921.iam.gserviceaccount.com"
}

import {
  to = google_project_iam_member.gke_nodes_default_node_sa
  id = "healthai-508921 roles/container.defaultNodeServiceAccount serviceAccount:healthai-gke-nodes@healthai-508921.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "gke_nodes_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:healthai-gke-nodes@healthai-508921.iam.gserviceaccount.com"
}

import {
  to = google_project_iam_member.gke_nodes_artifact_reader
  id = "healthai-508921 roles/artifactregistry.reader serviceAccount:healthai-gke-nodes@healthai-508921.iam.gserviceaccount.com"
}

# healthai-gke-app: Secret Manager Secret Accessor, Storage Object User
resource "google_project_iam_member" "gke_app_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:healthai-gke-app@healthai-508921.iam.gserviceaccount.com"
}

import {
  to = google_project_iam_member.gke_app_secret_accessor
  id = "healthai-508921 roles/secretmanager.secretAccessor serviceAccount:healthai-gke-app@healthai-508921.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "gke_app_storage_object_user" {
  project = var.project_id
  role    = "roles/storage.objectUser"
  member  = "serviceAccount:healthai-gke-app@healthai-508921.iam.gserviceaccount.com"
}

import {
  to = google_project_iam_member.gke_app_storage_object_user
  id = "healthai-508921 roles/storage.objectUser serviceAccount:healthai-gke-app@healthai-508921.iam.gserviceaccount.com"
}

# Workload Identity binding: lets the Kubernetes SA default/healthai-app impersonate
# healthai-gke-app. This is a binding ON the service account itself, not a project-level role.
resource "google_service_account_iam_member" "gke_app_workload_identity" {
  service_account_id = google_service_account.gke_app.name
  role                = "roles/iam.workloadIdentityUser"
  member              = "serviceAccount:healthai-508921.svc.id.goog[default/healthai-app]"
}

import {
  to = google_service_account_iam_member.gke_app_workload_identity
  id = "projects/healthai-508921/serviceAccounts/healthai-gke-app@healthai-508921.iam.gserviceaccount.com roles/iam.workloadIdentityUser serviceAccount:healthai-508921.svc.id.goog[default/healthai-app]"
}

# healthai-vm-sa: 5 roles (serves the old VM, kept until after the presentation)
resource "google_project_iam_member" "vm_sa_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:healthai-vm-sa@healthai-508921.iam.gserviceaccount.com"
}

import {
  to = google_project_iam_member.vm_sa_secret_accessor
  id = "healthai-508921 roles/secretmanager.secretAccessor serviceAccount:healthai-vm-sa@healthai-508921.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "vm_sa_storage_object_user" {
  project = var.project_id
  role    = "roles/storage.objectUser"
  member  = "serviceAccount:healthai-vm-sa@healthai-508921.iam.gserviceaccount.com"
}

import {
  to = google_project_iam_member.vm_sa_storage_object_user
  id = "healthai-508921 roles/storage.objectUser serviceAccount:healthai-vm-sa@healthai-508921.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "vm_sa_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:healthai-vm-sa@healthai-508921.iam.gserviceaccount.com"
}

import {
  to = google_project_iam_member.vm_sa_artifact_reader
  id = "healthai-508921 roles/artifactregistry.reader serviceAccount:healthai-vm-sa@healthai-508921.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "vm_sa_logs_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:healthai-vm-sa@healthai-508921.iam.gserviceaccount.com"
}

import {
  to = google_project_iam_member.vm_sa_logs_writer
  id = "healthai-508921 roles/logging.logWriter serviceAccount:healthai-vm-sa@healthai-508921.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "vm_sa_monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:healthai-vm-sa@healthai-508921.iam.gserviceaccount.com"
}

import {
  to = google_project_iam_member.vm_sa_monitoring_writer
  id = "healthai-508921 roles/monitoring.metricWriter serviceAccount:healthai-vm-sa@healthai-508921.iam.gserviceaccount.com"
}
