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
