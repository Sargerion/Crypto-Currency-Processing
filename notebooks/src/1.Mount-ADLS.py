# Databricks notebook source
# MAGIC %run ./Includes/Configuration

# COMMAND ----------

# Mount Bronze Storage (Raw area) with SAS

try: 
    dbutils.fs.mount(
    source = f"wasbs://{bronze}@{storage}.blob.core.windows.net/",
    mount_point = bronze_mount,
    extra_configs = {f"fs.azure.sas.{bronze}.{storage}.blob.core.windows.net":dbutils.secrets.get(scope = "crypto-db-scope", key = "crypto-adls-sas")}
)
except:
    print("Bronze already mounted!")

# COMMAND ----------

# Mount Silver Storage (Staged area) with SAS

try:
    dbutils.fs.mount(
    source = f"wasbs://{silver}@{storage}.blob.core.windows.net/",
    mount_point = silver_mount,
    extra_configs = {f"fs.azure.sas.{silver}.{storage}.blob.core.windows.net":dbutils.secrets.get(scope = "crypto-db-scope", key = "crypto-adls-sas")}
)
except:
    print("Silver already mounted!")

# COMMAND ----------

# Mount Gold Storage (Prepared area) with SAS

try:
    dbutils.fs.mount(
    source = f"wasbs://{gold}@{storage}.blob.core.windows.net/",
    mount_point = gold_mount,
    extra_configs = {f"fs.azure.sas.{gold}.{storage}.blob.core.windows.net":dbutils.secrets.get(scope = "crypto-db-scope", key = "crypto-adls-sas")}
)
except:
    print("Gold already mounted!")

# COMMAND ----------

# MAGIC %run ./Includes/Mkdirs

# COMMAND ----------

dbutils.fs.ls("/mnt")