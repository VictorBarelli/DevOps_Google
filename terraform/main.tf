# Enable necessary APIs
resource "google_project_service" "run_api" {
  service = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry_api" {
  service = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.repository_name
  description   = "Docker repository for Todo API"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry_api]
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "default" {
  name     = var.service_name
  location = var.region
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      # Placeholder image initially, will be replaced by the actual built image
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      
      ports {
        container_port = 8080
      }
    }
  }

  depends_on = [google_project_service.run_api]
}

# Allow unauthenticated access
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_v2_service.default.name
  location = google_cloud_run_v2_service.default.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
