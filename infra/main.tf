terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 7.0" }
    random = { source = "hashicorp/random", version = "~> 3.7" }
  }
}

variable "project_id" { type = string }
variable "billing_account" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}
variable "image" {
  type    = string
  default = ""
}
variable "deploy_app" {
  type    = bool
  default = false
}

provider "google" {
  project               = var.project_id
  region                = var.region
  billing_project       = var.project_id
  user_project_override = true
}

resource "google_project_service" "apis" {
  for_each           = toset(["run.googleapis.com", "sqladmin.googleapis.com", "storage.googleapis.com", "artifactregistry.googleapis.com", "cloudbuild.googleapis.com", "secretmanager.googleapis.com", "iam.googleapis.com", "cloudresourcemanager.googleapis.com", "billingbudgets.googleapis.com"])
  service            = each.value
  disable_on_destroy = false
}

resource "google_service_account" "app" {
  account_id   = "pdi-portal"
  display_name = "Portal PDI de demostración"
  depends_on   = [google_project_service.apis]
}
resource "google_service_account" "build" {
  account_id   = "pdi-build"
  display_name = "Compilación del portal PDI"
  depends_on   = [google_project_service.apis]
}
resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.app.email}"
}
resource "google_project_iam_member" "build_logs" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.build.email}"
}
resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = "pdi-images"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}
resource "google_artifact_registry_repository_iam_member" "build" {
  location   = var.region
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.build.email}"
}
resource "google_storage_bucket" "documents" {
  name                        = "${var.project_id}-documents"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  depends_on                  = [google_project_service.apis]
}
resource "google_storage_bucket_iam_member" "documents" {
  bucket = google_storage_bucket.documents.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.app.email}"
}
resource "google_storage_bucket" "build" {
  name                        = "${var.project_id}-build"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true
  lifecycle_rule {
    condition { age = 7 }
    action { type = "Delete" }
  }
  depends_on = [google_project_service.apis]
}
resource "google_storage_bucket_iam_member" "build" {
  bucket = google_storage_bucket.build.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.build.email}"
}
resource "google_storage_bucket_iam_member" "build_metadata" {
  bucket = google_storage_bucket.build.name
  role   = "roles/storage.legacyBucketReader"
  member = "serviceAccount:${google_service_account.build.email}"
}

resource "google_sql_database_instance" "postgres" {
  name                = "pdi-postgres"
  database_version    = "POSTGRES_16"
  region              = var.region
  deletion_protection = true
  settings {
    tier              = "db-f1-micro"
    edition           = "ENTERPRISE"
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10
    disk_autoresize   = false
    ip_configuration {
      ipv4_enabled = true
      ssl_mode     = "ENCRYPTED_ONLY"
      # Sin redes autorizadas: acceso mediante Cloud SQL Auth Proxy integrado.
    }
    backup_configuration {
      enabled                        = true
      start_time                     = "07:00"
      point_in_time_recovery_enabled = false
      backup_retention_settings { retained_backups = 3 }
    }
  }
  depends_on = [google_project_service.apis]
}
resource "google_sql_database" "portal" {
  name     = "portal"
  instance = google_sql_database_instance.postgres.name
}
resource "random_password" "database" {
  length  = 40
  special = false
}
resource "random_password" "session" {
  length  = 64
  special = false
}
resource "google_sql_user" "portal" {
  name     = "portal"
  instance = google_sql_database_instance.postgres.name
  password = random_password.database.result
}
resource "google_secret_manager_secret" "database" {
  secret_id = "pdi-db-password"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}
resource "google_secret_manager_secret_version" "database" {
  secret      = google_secret_manager_secret.database.id
  secret_data = random_password.database.result
}
resource "google_secret_manager_secret" "session" {
  secret_id = "pdi-session-secret"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}
resource "google_secret_manager_secret_version" "session" {
  secret      = google_secret_manager_secret.session.id
  secret_data = random_password.session.result
}
resource "google_secret_manager_secret_iam_member" "database" {
  secret_id = google_secret_manager_secret.database.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}
resource "google_secret_manager_secret_iam_member" "session" {
  secret_id = google_secret_manager_secret.session.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

resource "google_cloud_run_v2_service" "portal" {
  count               = var.deploy_app ? 1 : 0
  name                = "pdi-portal"
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"
  template {
    service_account                  = google_service_account.app.email
    timeout                          = "180s"
    max_instance_request_concurrency = 4
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
    volumes {
      name = "cloudsql"
      cloud_sql_instance { instances = [google_sql_database_instance.postgres.connection_name] }
    }
    containers {
      image = var.image
      resources {
        limits            = { cpu = "1", memory = "512Mi" }
        cpu_idle          = true
        startup_cpu_boost = true
      }
      ports { container_port = 8080 }
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
      env {
        name  = "DB_HOST"
        value = "/cloudsql/${google_sql_database_instance.postgres.connection_name}"
      }
      env {
        name  = "DB_NAME"
        value = google_sql_database.portal.name
      }
      env {
        name  = "DB_USER"
        value = google_sql_user.portal.name
      }
      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database.secret_id
            version = google_secret_manager_secret_version.database.version
          }
        }
      }
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.session.secret_id
            version = google_secret_manager_secret_version.session.version
          }
        }
      }
      env {
        name  = "DOCUMENT_BUCKET"
        value = google_storage_bucket.documents.name
      }
      env {
        name  = "CLOUD_DEPLOYMENT"
        value = "1"
      }
      dynamic "env" {
        for_each = var.azure_openai_endpoint != "" ? {
          AZURE_OPENAI_ENDPOINT   = var.azure_openai_endpoint
          AZURE_OPENAI_DEPLOYMENT = var.azure_openai_deployment
          AUTO_DOCUMENT_REVIEW    = var.auto_document_review ? "1" : "0"
        } : {}
        content {
          name  = env.key
          value = env.value
        }
      }
      dynamic "env" {
        for_each = var.azure_openai_key_secret != "" ? [var.azure_openai_key_secret] : []
        content {
          name = "AZURE_OPENAI_API_KEY"
          value_source {
            secret_key_ref {
              secret  = env.value
              version = var.azure_openai_key_version
            }
          }
        }
      }
    }
  }
  depends_on = [google_secret_manager_secret_iam_member.foundry, google_project_iam_member.sql_client, google_storage_bucket_iam_member.documents, google_secret_manager_secret_iam_member.database, google_secret_manager_secret_iam_member.session]
}
resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.deploy_app ? 1 : 0
  location = var.region
  name     = google_cloud_run_v2_service.portal[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "url" { value = var.deploy_app ? google_cloud_run_v2_service.portal[0].uri : null }
output "build_account" { value = google_service_account.build.email }
output "build_bucket" { value = google_storage_bucket.build.name }
output "image_repository" { value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}/portal" }

resource "google_billing_budget" "demo" {
  billing_account = var.billing_account
  display_name    = "PDI Lab 3 - avisos antes de agotar el crédito"
  budget_filter {
    projects               = ["projects/${data.google_project.current.number}"]
    credit_types_treatment = "EXCLUDE_ALL_CREDITS"
  }
  amount {
    specified_amount {
      currency_code = "USD"
      units         = "40"
    }
  }
  threshold_rules { threshold_percent = 0.25 }
  threshold_rules { threshold_percent = 0.5 }
  threshold_rules { threshold_percent = 0.75 }
  threshold_rules { threshold_percent = 1.0 }
  depends_on = [google_project_service.apis]
}
data "google_project" "current" { project_id = var.project_id }

# Optional Azure inference connection. Secrets remain outside Terraform state.
variable "azure_openai_endpoint" {
  type    = string
  default = ""
}
variable "azure_openai_deployment" {
  type    = string
  default = ""
}
variable "azure_openai_key_secret" {
  type    = string
  default = ""
}
variable "auto_document_review" {
  type    = bool
  default = false
}
resource "google_secret_manager_secret_iam_member" "foundry" {
  count     = var.azure_openai_key_secret != "" ? 1 : 0
  secret_id = var.azure_openai_key_secret
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

variable "azure_openai_key_version" {
  type    = string
  default = "latest"
}
