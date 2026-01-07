# Cloud Monitoring setup

# Enable Monitoring API
resource "google_project_service" "monitoring_api" {
  service            = "monitoring.googleapis.com"
  disable_on_destroy = false
}

# Notification Channel (Email)
resource "google_monitoring_notification_channel" "email" {
  display_name = "DevOps Admin Email"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
  
  depends_on = [google_project_service.monitoring_api]
}

# Alert policies

# Alert: High Error Rate (5xx errors > 1% of requests)
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "Cloud Run - High Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate exceeds 1%"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
      
      trigger {
        count = 1
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "604800s" # 7 days
  }
  
  documentation {
    content   = "The Cloud Run service ${var.service_name} is experiencing a high rate of 5xx errors. Please investigate immediately."
    mime_type = "text/markdown"
  }
  
  depends_on = [google_project_service.monitoring_api]
}

# Alert: High Latency (p99 > 5 seconds)
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "Cloud Run - High Latency"
  combiner     = "OR"
  
  conditions {
    display_name = "Request latency exceeds 5 seconds"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5000 # 5 seconds in milliseconds
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_99"
      }
      
      trigger {
        count = 1
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "604800s"
  }
  
  documentation {
    content   = "The Cloud Run service ${var.service_name} is experiencing high latency (p99 > 5s). Consider scaling up or optimizing the application."
    mime_type = "text/markdown"
  }
  
  depends_on = [google_project_service.monitoring_api]
}

# Alert: Instance Count Spike
resource "google_monitoring_alert_policy" "instance_count_spike" {
  display_name = "Cloud Run - High Instance Count"
  combiner     = "OR"
  
  conditions {
    display_name = "Instance count exceeds threshold"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/container/instance_count\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MAX"
      }
      
      trigger {
        count = 1
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "604800s"
  }
  
  documentation {
    content   = "The Cloud Run service ${var.service_name} has scaled to more than 10 instances. This may indicate high traffic or a potential issue."
    mime_type = "text/markdown"
  }
  
  depends_on = [google_project_service.monitoring_api]
}

# Uptime check config

resource "google_monitoring_uptime_check_config" "health_check" {
  display_name = "DevOps Dashboard Health Check"
  timeout      = "10s"
  period       = "60s"
  
  http_check {
    path         = "/api/status"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }
  
  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = "${var.service_name}-${var.project_id}.${var.region}.run.app"
    }
  }
  
  depends_on = [google_project_service.monitoring_api]
}

# Alert: Uptime Check Failed
resource "google_monitoring_alert_policy" "uptime_check_failed" {
  display_name = "Cloud Run - Service Unavailable"
  combiner     = "OR"
  
  conditions {
    display_name = "Uptime check failed"
    
    condition_threshold {
      filter          = "resource.type = \"uptime_url\" AND metric.type = \"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.labels.check_id = \"${google_monitoring_uptime_check_config.health_check.uptime_check_id}\""
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_FRACTION_TRUE"
        cross_series_reducer = "REDUCE_MIN"
        group_by_fields      = ["resource.label.host"]
      }
      
      trigger {
        count = 1
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "604800s"
  }
  
  documentation {
    content   = "The uptime check for ${var.service_name} has failed. The service may be down or unreachable."
    mime_type = "text/markdown"
  }
  
  depends_on = [google_monitoring_uptime_check_config.health_check]
}
