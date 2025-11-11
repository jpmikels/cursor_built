variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "region" {
  description = "Primary GCP region"
  type        = string
  default     = "us-central1"
}

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-custom-2-7680" # 2 vCPU, 7.68 GB RAM
}

variable "db_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 50
}

variable "backend_max_instances" {
  description = "Maximum number of backend Cloud Run instances"
  type        = number
  default     = 10
}

variable "frontend_max_instances" {
  description = "Maximum number of frontend Cloud Run instances"
  type        = number
  default     = 5
}

variable "uploads_retention_days" {
  description = "Number of days to retain uploaded files"
  type        = number
  default     = 365
}

variable "artifacts_retention_days" {
  description = "Number of days to retain generated artifacts"
  type        = number
  default     = 730
}

variable "github_repo" {
  description = "GitHub repository in format owner/repo"
  type        = string
}

variable "alert_email" {
  description = "Email address for monitoring alerts"
  type        = string
}

