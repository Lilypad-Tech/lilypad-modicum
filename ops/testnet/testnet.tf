# provider "google" {
#   project = "bacalhau-production"
#   region  = "us-central1"
#   zone    = "us-central1-a"
# }

# terraform {
#   backend "gcs" {
#     # this bucket lives in the bacalhau-cicd google project
#     # https://console.cloud.google.com/storage/browser/bacalhau-global-storage;tab=objects?project=bacalhau-cicd
#     bucket = "bacalhau-global-storage"
#     prefix = "bravo-testnet/terraform"
#   }
# }

# // A single Google Cloud Engine instance
# resource "google_compute_instance" "bravo-testnet-vm" {
#   name         = "bravo-testnet-vm-0"
#   machine_type = "e2-standard-4"
#   zone         = "us-central1-a"

#   boot_disk {
#     initialize_params {
#       image = "ubuntu-os-cloud/ubuntu-2204-lts"
#       size  = 100 # Gb
#     }
#   }

#   network_interface {
#     network    = google_compute_network.bravo_testnet_network.name
#     access_config {
#       nat_ip = google_compute_address.ipv4_address.address
#     }
#   }

#   lifecycle {
#     ignore_changes = [attached_disk]
#   }

#   allow_stopping_for_update = true

#   metadata_startup_script = <<-EOF
# #!/bin/bash
# set -euo pipefail
# IFS=$'\n\t'

# echo "Installing packages"

# sudo apt-get update
# sudo apt-get -y install docker.io

# echo "Mounting disk"

# # wait for /dev/sdb to exist
# while [[ ! -e /dev/sdb ]]; do
#   sleep 1
#   echo "waiting for /dev/sdb to exist"
# done

# # mount /dev/sdb at /data
# sudo mkdir -p /data
# sudo mount /dev/sdb /data || (sudo mkfs -t ext4 /dev/sdb && sudo mount /dev/sdb /data)
# EOF
# }

# resource "google_compute_network" "bravo_testnet_network" {
#   name                    = "bravo-testnet-network"
# }

# resource "google_compute_address" "ipv4_address" {
#   region = "us-central1"
#   name   = "bravo-testnet-ipv4-address"
#   lifecycle {
#     prevent_destroy = true
#   }
# }

# output "public_ip_address" {
#   value = google_compute_instance.bravo-testnet-vm.network_interface[0].access_config[0].nat_ip
# }

# resource "google_compute_firewall" "bravo_testnet_ssh_firewall" {
#   name    = "bravo-testnet-ssh-firewall"
#   network = google_compute_network.bravo_testnet_network.name

#   allow {
#     protocol = "icmp"
#   }

#   allow {
#     protocol = "tcp"
#     ports = [
#       "22",
#       "80",
#       "443",
#       "8545"
#     ]
#   }

#   source_ranges = ["0.0.0.0/0"]
# }

# resource "google_compute_disk" "data_disk" {
#   # keep the same disk names if we are production because the libp2p ids are in the auto connect serve codebase
#   name     = "bravo-testnet-data-disk"
#   type     = "pd-ssd"
#   zone     = "us-central1-a"
#   size     = 1024
#   lifecycle {
#     prevent_destroy = true
#   }
# }

# resource "google_compute_disk_resource_policy_attachment" "attachment" {
#   name  = google_compute_resource_policy.data_disk_backups.name
#   disk  = google_compute_disk.data_disk.name
#   zone  = "us-central1-a"
# }

# resource "google_compute_resource_policy" "data_disk_backups" {
#   name   = "data-disk-backups-bravo-testnet"
#   region = "us-central1"
#   snapshot_schedule_policy {
#     schedule {
#       daily_schedule {
#         days_in_cycle = 1
#         start_time    = "23:00"
#       }
#     }
#     retention_policy {
#       max_retention_days    = 30
#       on_source_disk_delete = "KEEP_AUTO_SNAPSHOTS"
#     }
#     snapshot_properties {
#       labels = {
#         waterlily_backup = "true"
#       }
#       # this only works with Windows and looks like it's non-negotiable with gcp
#       guest_flush = false
#     }
#   }
# }

# resource "google_compute_attached_disk" "default" {
#   disk     = google_compute_disk.data_disk.self_link
#   instance = google_compute_instance.bravo-testnet-vm.self_link
#   zone     = "us-central1-a"
# }
