variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The Google Cloud region to deploy resources"
  type        = string
  default     = "us-east1"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "devops-google"
}

variable "repository_name" {
  description = "The name of the Artifact Registry repository"
  type        = string
  default     = "cloud-run-source-deploy"
}

variable "alert_email" {
  description = "Email address for monitoring alerts"
  type        = string
  default     = "admin@example.com"
}
