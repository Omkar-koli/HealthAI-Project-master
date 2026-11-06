# Global static IP used by the Ingress (healthai-ingress). Imported.
# This is in the "Must keep" list, not slated for deletion with the old VM leftovers.
resource "google_compute_global_address" "lb_ip" {
  project = var.project_id
  name    = "healthai-lb-ip"
}

import {
  to = google_compute_global_address.lb_ip
  id = "projects/healthai-508921/global/addresses/healthai-lb-ip"
}
