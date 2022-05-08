terraform {
  backend "azurerm" {
    subscription_id       = "${SUBSCRIPTION_ID}"
    resource_group_name   = "rg-crypto"
    storage_account_name  = "cryptostorage"
    container_name        = "tfstate"
    key                   = "crypto-201.tfstate"
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "bdcc" {
  name = "rg-${var.ENV}-${var.LOCATION}"
  location = var.LOCATION

  lifecycle {
    prevent_destroy = false
  }

  tags = {
    region = var.BDCC_REGION
    env = var.ENV
  }
}

resource "azurerm_storage_account" "bdcc" {
  depends_on = [
    azurerm_resource_group.bdcc]

  name = "st${var.ENV}${var.LOCATION}"
  resource_group_name = azurerm_resource_group.bdcc.name
  location = azurerm_resource_group.bdcc.location
  account_tier = "Standard"
  account_kind = "StorageV2"
  account_replication_type = var.STORAGE_ACCOUNT_REPLICATION_TYPE
  is_hns_enabled = "true"

  network_rules {
    default_action = "Allow"
  }

  lifecycle {
    prevent_destroy = false
  }

  tags = {
    region = var.BDCC_REGION
    env = var.ENV
  }
}

resource "azurerm_storage_container" "bronze" {
  name                  = "bronze-crypto"
  storage_account_name  = azurerm_storage_account.bdcc.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver-crypto"
  storage_account_name  = azurerm_storage_account.bdcc.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold-crypto"
  storage_account_name  = azurerm_storage_account.bdcc.name
  container_access_type = "private"
}

resource "azurerm_eventhub_namespace" "eventhub-namespace" {
  name                = "crypto-eventhub201"
  location            = azurerm_resource_group.bdcc.location
  resource_group_name = azurerm_resource_group.bdcc.name
  sku                 = "Standard"
  capacity            = 2

  tags = {
    region = var.BDCC_REGION
    env = var.ENV
  }

  lifecycle {
    prevent_destroy = false
  }
}

resource "azurerm_eventhub" "eventhub" {
  name = "cryptohub201"
  namespace_name = azurerm_eventhub_namespace.eventhub-namespace.name
  resource_group_name = azurerm_resource_group.bdcc.name
  partition_count = 4
  message_retention = 3

  capture_description {
    enabled  = true
    encoding = "Avro"
    interval_in_seconds = 60
    skip_empty_archives = true
    destination {
      archive_name_format = "{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}"
      blob_container_name = azurerm_storage_container.bronze.name
      name                = "EventHubArchive.AzureBlockBlob"
      storage_account_id  = azurerm_storage_account.bdcc.id
    }
  }
}

resource "azurerm_data_factory" "adf" {
  name                = "crypto-adf201"
  location            = azurerm_resource_group.bdcc.location
  resource_group_name = azurerm_resource_group.bdcc.name
}

resource "azurerm_databricks_workspace" "bdcc" {
  depends_on = [
    azurerm_resource_group.bdcc
  ]

  name = "dbw-${var.ENV}-${var.LOCATION}"
  resource_group_name = azurerm_resource_group.bdcc.name
  location = azurerm_resource_group.bdcc.location
  sku = "standard"

  tags = {
    region = var.BDCC_REGION
    env = var.ENV
  }
}

resource "azurerm_key_vault" "key-vault" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name

  enabled_for_deployment          = var.enabled_for_deployment
  enabled_for_disk_encryption     = var.enabled_for_disk_encryption
  enabled_for_template_deployment = var.enabled_for_template_deployment

  tenant_id = data.azurerm_client_config.current.tenant_id
  sku_name  = var.sku_name
  tags      = var.tags

  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }
}

resource "azurerm_key_vault_access_policy" "default_policy" {
  key_vault_id = azurerm_key_vault.key-vault.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  lifecycle {
    create_before_destroy = true
  }

  key_permissions = var.kv-key-permissions-full
  secret_permissions = var.kv-secret-permissions-full
  certificate_permissions = var.kv-certificate-permissions-full
  storage_permissions = var.kv-storage-permissions-full
}

resource "azurerm_key_vault_access_policy" "policy" {
  for_each                = var.policies
  key_vault_id            = azurerm_key_vault.key-vault.id
  tenant_id               = lookup(each.value, "tenant_id")
  object_id               = lookup(each.value, "object_id")
  key_permissions         = lookup(each.value, "key_permissions")
  secret_permissions      = lookup(each.value, "secret_permissions")
  certificate_permissions = lookup(each.value, "certificate_permissions")
  storage_permissions     = lookup(each.value, "storage_permissions")
}
