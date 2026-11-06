# ---------------------------------------------------------------------------
# Milestone 6, Phase 3: observability resources. These are NEW — created by
# Terraform from scratch, not imported (there was nothing to import).
# ---------------------------------------------------------------------------

# Log-based metric: counts backend requests whose JSON status field is >= 500.
# This is the exact filter we validated by hand in Logs Explorer earlier.
resource "google_logging_metric" "backend_5xx" {
  project = var.project_id
  name    = "backend-5xx-count"
  filter  = <<-EOT
    resource.type="k8s_container"
    resource.labels.container_name="backend"
    jsonPayload.status>=500
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

# One email notification channel per teammate.
resource "google_monitoring_notification_channel" "email" {
  for_each     = toset(var.alert_emails)
  project      = var.project_id
  display_name = "HealthAI team - ${each.value}"
  type         = "email"

  labels = {
    email_address = each.value
  }
}

# Alert policy: fires when the 5xx metric is above 0 in any 60-second window.
# Threshold of 0 (i.e. "any 5xx at all") is deliberate for the demo, so pressing
# the diagnostics button reliably produces a visible alert.
resource "google_monitoring_alert_policy" "backend_5xx" {
  project      = var.project_id
  display_name = "HealthAI backend 5xx errors"
  combiner     = "OR"

  conditions {
    display_name = "Backend 5xx count > 0"

    condition_threshold {
      filter          = "resource.type=\"k8s_container\" AND metric.type=\"logging.googleapis.com/user/${google_logging_metric.backend_5xx.name}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_COUNT"
      }
    }
  }

  notification_channels = [for channel in google_monitoring_notification_channel.email : channel.name]

  alert_strategy {
    auto_close = "1800s"
  }
}
