terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      # Loose range on purpose: terraform init will fetch the latest 5.x or 6.x
      # release automatically, so this doesn't need to be re-pinned by hand.
      version = ">= 5.0, < 7.0"
    }
  }

  # Remote state in the versioned bucket created by hand (gcloud storage
  # buckets create ... gs://healthai-508921-tfstate), per the Terraform scope
  # table: the state bucket itself is NOT managed by Terraform.
  backend "gcs" {
    bucket = "healthai-508921-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
