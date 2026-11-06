# Cloud SQL instance + database (Milestone 4). Users (postgres, healthai_app)
# are NOT managed here — they're created by the SQL migration files, per the
# Terraform scope table.
#
# NOTE: the brief warns the plan only reads clean while the instance's
# activation policy is ALWAYS (i.e. running). Don't stop the database before
# running "terraform plan" against this resource.
resource "google_sql_database_instance" "healthai_pg" {
  project          = var.project_id
  name             = "healthai-pg"
  region           = var.region
  database_version = "POSTGRES_15"

  settings {
    tier                         = "db-f1-micro"
    edition                      = "ENTERPRISE"
    availability_type            = "ZONAL"
    deletion_protection_enabled  = true
    enable_dataplex_integration  = true
    retain_backups_on_delete     = true

    ip_configuration {
      ipv4_enabled    = false
      private_network = "projects/${var.project_id}/global/networks/default"

      psc_config {
        psc_enabled               = false
        allowed_consumer_projects = []
      }
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = false
      location                       = "us"
    }

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    password_validation_policy {
      enable_password_policy      = true
      complexity                  = "COMPLEXITY_DEFAULT"
      disallow_username_substring = true
      min_length                  = 8
      reuse_interval              = 0
    }
  }

  # Safety net: don't let "terraform destroy" ever delete the real database by accident.
  deletion_protection = true

  # The real instance reports a maintenance_window with day=0 (GCP's internal
  # "no preference set" value), but the provider only accepts 1-7 when writing
  # it. That makes this field impossible to declare without either a provider
  # error or a perpetual diff, so this tells Terraform to ignore drift on it.
  lifecycle {
    ignore_changes = [settings[0].maintenance_window]
  }
}

import {
  to = google_sql_database_instance.healthai_pg
  id = "healthai-508921/healthai-pg"
}

resource "google_sql_database" "healthai" {
  project  = var.project_id
  instance = google_sql_database_instance.healthai_pg.name
  name     = "healthai"
}

import {
  to = google_sql_database.healthai
  id = "healthai-508921/healthai-pg/healthai"
}
