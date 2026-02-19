output "kubeconfig" {
  value     = linode_lke_cluster.incident_copilot.kubeconfig
  sensitive = true
}

output "cluster_id" {
  value = linode_lke_cluster.incident_copilot.id
}

output "status" {
  value = linode_lke_cluster.incident_copilot.status
}

output "api_endpoints" {
  value     = linode_lke_cluster.incident_copilot.api_endpoints
  sensitive = true
}
