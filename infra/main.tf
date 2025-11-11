terraform {
  required_version = ">= 1.5"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "gcs" {
    # Configure with: terraform init -backend-config="bucket=your-terraform-state-bucket"
    prefix = "vwb/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "secretmanager.googleapis.com",
    "documentai.googleapis.com",
    "aiplatform.googleapis.com",
    "workflows.googleapis.com",
    "cloudtasks.googleapis.com",
    "artifactregistry.googleapis.com",
    "vpcaccess.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ])

  service            = each.key
  disable_on_destroy = false
}

# Random suffix for globally unique names
resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  name_prefix = "${var.project_id}-${var.environment}"
  common_labels = {
    environment = var.environment
    application = "vwb"
    managed_by  = "terraform"
  }
}

# ========================================
# Cloud Storage Buckets
# ========================================

resource "google_storage_bucket" "uploads" {
  name          = "${local.name_prefix}-vwb-uploads-${random_id.suffix.hex}"
  location      = var.region
  force_destroy = var.environment != "prod"
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = var.uploads_retention_days
    }
    action {
      type = "Delete"
    }
  }
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

resource "google_storage_bucket" "artifacts" {
  name          = "${local.name_prefix}-vwb-artifacts-${random_id.suffix.hex}"
  location      = var.region
  force_destroy = var.environment != "prod"
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = var.artifacts_retention_days
    }
    action {
      type = "Delete"
    }
  }
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

# ========================================
# BigQuery Datasets
# ========================================

resource "google_bigquery_dataset" "raw" {
  dataset_id    = "vwb_raw_${var.environment}"
  friendly_name = "VWB Raw Data"
  description   = "Raw extracted data from documents"
  location      = var.region
  
  default_table_expiration_ms = var.environment == "dev" ? 7776000000 : null # 90 days for dev
  
  labels = local.common_labels
  
  access {
    role          = "OWNER"
    user_by_email = google_service_account.backend.email
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_bigquery_dataset" "curated" {
  dataset_id    = "vwb_curated_${var.environment}"
  friendly_name = "VWB Curated Data"
  description   = "Normalized and validated financial data"
  location      = var.region
  
  labels = local.common_labels
  
  access {
    role          = "OWNER"
    user_by_email = google_service_account.backend.email
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_bigquery_dataset" "valuation" {
  dataset_id    = "vwb_valuation_${var.environment}"
  friendly_name = "VWB Valuation"
  description   = "Valuation runs and outputs"
  location      = var.region
  
  labels = local.common_labels
  
  access {
    role          = "OWNER"
    user_by_email = google_service_account.backend.email
  }
  
  depends_on = [google_project_service.required_apis]
}

# BigQuery tables will be created by application migrations

# ========================================
# Cloud SQL (PostgreSQL)
# ========================================

resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "google_sql_database_instance" "postgres" {
  name             = "${local.name_prefix}-vwb-db-${random_id.suffix.hex}"
  database_version = "POSTGRES_15"
  region           = var.region
  
  deletion_protection = var.environment == "prod"
  
  settings {
    tier              = var.db_tier
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = var.db_disk_size
    disk_autoresize   = true
    
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
      }
    }
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }
    
    database_flags {
      name  = "max_connections"
      value = "100"
    }
    
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    
    insights_config {
      query_insights_enabled  = true
      query_plans_per_minute  = 5
      query_string_length     = 1024
      record_application_tags = true
    }
    
    user_labels = local.common_labels
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

resource "google_sql_database" "vwb" {
  name     = "vwb"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "vwb_user" {
  name     = "vwb_app"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# ========================================
# Networking (VPC for Cloud SQL)
# ========================================

resource "google_compute_network" "vpc" {
  name                    = "${local.name_prefix}-vwb-vpc"
  auto_create_subnetworks = false
  
  depends_on = [google_project_service.required_apis]
}

resource "google_compute_global_address" "private_ip_range" {
  name          = "${local.name_prefix}-vwb-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
  
  depends_on = [google_project_service.required_apis]
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
  
  depends_on = [google_project_service.required_apis]
}

resource "google_vpc_access_connector" "connector" {
  name          = "${local.name_prefix}-vwb-vpc-cx"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
  
  machine_type  = "e2-micro"
  min_instances = 2
  max_instances = 3
  
  depends_on = [google_project_service.required_apis]
}

# ========================================
# Pub/Sub Topics & Subscriptions
# ========================================

resource "google_pubsub_topic" "ingestion_requested" {
  name = "${local.name_prefix}-vwb-ingestion-requested"
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_subscription" "ingestion_requested_sub" {
  name  = "${local.name_prefix}-vwb-ingestion-requested-sub"
  topic = google_pubsub_topic.ingestion_requested.name
  
  ack_deadline_seconds = 600
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_topic" "validation_completed" {
  name = "${local.name_prefix}-vwb-validation-completed"
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_topic" "dead_letter" {
  name = "${local.name_prefix}-vwb-dead-letter"
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

# ========================================
# Cloud Tasks Queue
# ========================================

resource "google_cloud_tasks_queue" "valuation_queue" {
  name     = "${local.name_prefix}-vwb-valuation-queue"
  location = var.region
  
  rate_limits {
    max_concurrent_dispatches = 10
    max_dispatches_per_second = 5
  }
  
  retry_config {
    max_attempts       = 3
    max_retry_duration = "3600s"
    min_backoff        = "60s"
    max_backoff        = "600s"
    max_doublings      = 3
  }
  
  depends_on = [google_project_service.required_apis]
}

# ========================================
# Secret Manager
# ========================================

resource "google_secret_manager_secret" "db_password" {
  secret_id = "${local.name_prefix}-vwb-db-password"
  
  replication {
    auto {}
  }
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "${local.name_prefix}-vwb-jwt-secret"
  
  replication {
    auto {}
  }
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = random_password.jwt_secret.result
}

# Placeholder secrets for market data providers (to be populated manually)
resource "google_secret_manager_secret" "pitchbook_api_key" {
  secret_id = "${local.name_prefix}-vwb-pitchbook-key"
  
  replication {
    auto {}
  }
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret" "capiq_api_key" {
  secret_id = "${local.name_prefix}-vwb-capiq-key"
  
  replication {
    auto {}
  }
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

# ========================================
# Service Accounts
# ========================================

resource "google_service_account" "backend" {
  account_id   = "${var.environment}-vwb-backend"
  display_name = "VWB Backend Service Account"
  description  = "Service account for VWB backend Cloud Run service"
  
  depends_on = [google_project_service.required_apis]
}

resource "google_service_account" "frontend" {
  account_id   = "${var.environment}-vwb-frontend"
  display_name = "VWB Frontend Service Account"
  description  = "Service account for VWB frontend Cloud Run service"
  
  depends_on = [google_project_service.required_apis]
}

resource "google_service_account" "cloudbuild" {
  account_id   = "${var.environment}-vwb-cloudbuild"
  display_name = "VWB Cloud Build Service Account"
  description  = "Service account for VWB Cloud Build pipelines"
  
  depends_on = [google_project_service.required_apis]
}

# ========================================
# IAM Bindings
# ========================================

# Backend service account permissions
resource "google_project_iam_member" "backend_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_documentai_user" {
  project = var.project_id
  role    = "roles/documentai.apiUser"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_cloudtasks_enqueuer" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Cloud Build service account permissions
resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

resource "google_project_iam_member" "cloudbuild_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

resource "google_project_iam_member" "cloudbuild_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

resource "google_project_iam_member" "cloudbuild_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

resource "google_project_iam_member" "cloudbuild_sql_admin" {
  project = var.project_id
  role    = "roles/cloudsql.admin"
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

# ========================================
# Artifact Registry
# ========================================

resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = "${var.environment}-vwb-docker"
  description   = "Docker repository for VWB container images"
  format        = "DOCKER"
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

# ========================================
# Cloud Run Services
# ========================================

resource "google_cloud_run_v2_service" "backend" {
  name     = "${local.name_prefix}-vwb-backend"
  location = var.region
  
  template {
    service_account = google_service_account.backend.email
    
    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = var.backend_max_instances
    }
    
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
    
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}/backend:latest"
      
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
        cpu_idle = true
      }
      
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      
      env {
        name  = "REGION"
        value = var.region
      }
      
      env {
        name  = "UPLOADS_BUCKET"
        value = google_storage_bucket.uploads.name
      }
      
      env {
        name  = "ARTIFACTS_BUCKET"
        value = google_storage_bucket.artifacts.name
      }
      
      env {
        name  = "BQ_DATASET_RAW"
        value = google_bigquery_dataset.raw.dataset_id
      }
      
      env {
        name  = "BQ_DATASET_CURATED"
        value = google_bigquery_dataset.curated.dataset_id
      }
      
      env {
        name  = "BQ_DATASET_VALUATION"
        value = google_bigquery_dataset.valuation.dataset_id
      }
      
      env {
        name  = "DB_HOST"
        value = google_sql_database_instance.postgres.private_ip_address
      }
      
      env {
        name  = "DB_NAME"
        value = google_sql_database.vwb.name
      }
      
      env {
        name  = "DB_USER"
        value = google_sql_user.vwb_user.name
      }
      
      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "JWT_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jwt_secret.secret_id
            version = "latest"
          }
        }
      }
      
      ports {
        container_port = 8080
      }
      
      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 3
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 30
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }
    }
    
    timeout = "600s"
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_vpc_access_connector.connector,
  ]
  
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }
}

resource "google_cloud_run_v2_service" "frontend" {
  name     = "${local.name_prefix}-vwb-frontend"
  location = var.region
  
  template {
    service_account = google_service_account.frontend.email
    
    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = var.frontend_max_instances
    }
    
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}/frontend:latest"
      
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }
      
      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
      
      env {
        name  = "NEXT_PUBLIC_ENVIRONMENT"
        value = var.environment
      }
      
      ports {
        container_port = 3000
      }
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  depends_on = [google_project_service.required_apis]
  
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }
}

# Allow public access to Cloud Run services
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = google_cloud_run_v2_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ========================================
# Workload Identity Federation for GitHub
# ========================================

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "${var.environment}-vwb-github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
  
  depends_on = [google_project_service.required_apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "${var.environment}-vwb-github-provider"
  display_name                       = "GitHub Actions Provider"
  description                        = "OIDC provider for GitHub Actions"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  
  attribute_condition = "assertion.repository == '${var.github_repo}'"
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_service_account_iam_member" "github_cloudbuild" {
  service_account_id = google_service_account.cloudbuild.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

# ========================================
# Cloud Build Trigger
# ========================================

resource "google_cloudbuild_trigger" "main_push" {
  name        = "${local.name_prefix}-vwb-main-push"
  description = "Build and deploy on push to main branch"
  
  github {
    owner = split("/", var.github_repo)[0]
    name  = split("/", var.github_repo)[1]
    push {
      branch = "^main$"
    }
  }
  
  filename = "infra/cloudbuild.yaml"
  
  service_account = google_service_account.cloudbuild.id
  
  substitutions = {
    _ENVIRONMENT        = var.environment
    _REGION             = var.region
    _ARTIFACT_REGISTRY  = google_artifact_registry_repository.docker.name
    _BACKEND_SERVICE    = google_cloud_run_v2_service.backend.name
    _FRONTEND_SERVICE   = google_cloud_run_v2_service.frontend.name
    _DB_INSTANCE        = google_sql_database_instance.postgres.connection_name
  }
  
  depends_on = [google_project_service.required_apis]
}

# ========================================
# Monitoring & Alerting
# ========================================

resource "google_monitoring_notification_channel" "email" {
  display_name = "VWB Alert Email"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
  
  enabled = true
  
  depends_on = [google_project_service.required_apis]
}

resource "google_monitoring_alert_policy" "backend_error_rate" {
  display_name = "VWB Backend High Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate > 5%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${google_cloud_run_v2_service.backend.name}\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.id]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_monitoring_alert_policy" "backend_latency" {
  display_name = "VWB Backend High Latency"
  combiner     = "OR"
  
  conditions {
    display_name = "P95 latency > 3s"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${google_cloud_run_v2_service.backend.name}\" AND metric.type=\"run.googleapis.com/request_latencies\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 3000
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.id]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  depends_on = [google_project_service.required_apis]
}

# ========================================
# Log Sinks
# ========================================

resource "google_logging_project_sink" "error_sink" {
  name        = "${local.name_prefix}-vwb-error-sink"
  destination = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${google_bigquery_dataset.raw.dataset_id}"
  
  filter = "severity >= ERROR AND (resource.type=\"cloud_run_revision\" OR resource.type=\"cloud_function\")"
  
  unique_writer_identity = true
  
  bigquery_options {
    use_partitioned_tables = true
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_bigquery_dataset_iam_member" "error_sink_writer" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.error_sink.writer_identity
}

