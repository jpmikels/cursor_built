output "backend_url" {
  description = "URL of the backend Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "URL of the frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "uploads_bucket" {
  description = "GCS bucket for uploads"
  value       = google_storage_bucket.uploads.name
}

output "artifacts_bucket" {
  description = "GCS bucket for artifacts"
  value       = google_storage_bucket.artifacts.name
}

output "db_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "db_private_ip" {
  description = "Cloud SQL private IP address"
  value       = google_sql_database_instance.postgres.private_ip_address
  sensitive   = true
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}

output "backend_service_account" {
  description = "Backend service account email"
  value       = google_service_account.backend.email
}

output "frontend_service_account" {
  description = "Frontend service account email"
  value       = google_service_account.frontend.email
}

output "cloudbuild_service_account" {
  description = "Cloud Build service account email"
  value       = google_service_account.cloudbuild.email
}

output "workload_identity_provider" {
  description = "Workload Identity Provider for GitHub Actions"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "bigquery_datasets" {
  description = "BigQuery dataset IDs"
  value = {
    raw       = google_bigquery_dataset.raw.dataset_id
    curated   = google_bigquery_dataset.curated.dataset_id
    valuation = google_bigquery_dataset.valuation.dataset_id
  }
}

output "pubsub_topics" {
  description = "Pub/Sub topic names"
  value = {
    ingestion_requested   = google_pubsub_topic.ingestion_requested.name
    validation_completed  = google_pubsub_topic.validation_completed.name
    dead_letter           = google_pubsub_topic.dead_letter.name
  }
}

