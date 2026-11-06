variable "project_id" {
  description = "GCP project ID that holds the HealthAI infrastructure."
  type        = string
  default     = "healthai-508921"
}

variable "region" {
  description = "Primary region for HealthAI's resources."
  type        = string
  default     = "us-central1"
}

variable "alert_emails" {
  description = "Team email addresses that receive the Milestone 6 5xx alert."
  type        = list(string)
  default = [
    "sranjan@cougarnet.uh.edu",
    "sdamera@cougarnet.uh.edu",
    "okoli@cougarnet.uh.edu",
    "sathomas26@cougarnet.uh.edu",
    "aedachal@cougarnet.uh.edu",
  ]
}
