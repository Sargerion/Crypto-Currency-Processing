# Crypto currency project

This project takes crypto currency (Bitcoin, Ethereum) data 
from REST API (finnhub.io), loads them into **Azure EventHub**. From there,
this data gets captured and stored into **Azure Data Lake Storage** Raw Area, then it gets cleaned
and written by Spark Structured Stream to Staged Area. From this area it goes
to **MongoDB Atlas** (By **Azure Data Factory** Copy Activity) and gets processed by 
Spark Structured Stream (aggregations, business values) and written to Prepared
Area while simultaneously being displayed at **PowerBI Dashboard**

![](screenshots/Crypto_Architecture.PNG)

### Requierments:
* Active Azure Subscription (Standard or Premium)
* MongoDB Atlas (follow this guide to register)  
https://cloudnodelab.azurewebsites.net/provisioning-a-mongodb-atlas-cluster-to-azure/  
* Terraform  
https://learn.hashicorp.com/tutorials/terraform/install-cli
* PowerBI Desktop  
https://powerbi.microsoft.com/en-us/desktop/

### Tools used:
* Cloud service - **Microsoft Azure**
* Infrastructure deployment - **Terraform**
* Scheduling & orchestration - **Data Factory**
* Messaging system - **Event Hub**
* Data processing - **Apache Spark (Databricks)**
* Storage:
    * Data lake - **Data Lake Storage Gen 2**
    * Database - **MongoDB Atlas**
* Reporting - **Power BI Desktop**

### 1. Create Azure resources using terraform  
``` 
az login
terraform init
```
![](screenshots/1.Terraform_init.PNG)

```
terraform plan -out=crypto-plan
```

![](screenshots/2.Terraform_plan.PNG)

```
terraform apply "crypto-plan"
```

![](screenshots/3.Terraform_apply_1.PNG)

Wait about 5 minutes for plan to apply

![](screenshots/4.Terraform_apply_2.PNG)

### 2. Configure security (tokens, secrets)
* ADLS Token  

Go to Storage Account on Azure, select **"Shared acces signature"**
under **"Security + networking"** tab

![](screenshots/5.SAS.PNG)

Check allowed resources type and increase expiration date

![](screenshots/6.SAS_check.PNG)

Generate SAS. Save **SAS token** field, you will need it later

![](screenshots/7.SAS_gen.PNG)

* EventHub Connection String

Go to **EventHub** namespace, **“Shared access policies”** under **“Settings”** tab. Choose **RootManageSharedAccessKey**  

Save **“Connection string–primary key”** 

![](screenshots/8.Eventhub_SAS.PNG)

![](screenshots/9.Eventhub_conn_str.PNG)

Now go to **KeyVault** and create two secrets for **ADLS** and **EventHub** with values from previous steps

![](screenshots/10.Keyvault.PNG)

![](screenshots/11.Keyvault_secret_adls.PNG)
![](screenshots/12.Keyvault_eventhub.PNG)

* Databricks secret scope  
Now to link Datbricks with Azure KeyVault we need to create secret scope
(there is no button on UI, so you have to do it using **Databricks CLI** or by adding 
**#secrets/createScope** to workspace URL. In this example I will go with the latter

First, open KeyVault in another tab, then go to **"Properties"** under **"Settings"** tab
We will need two fields: **"Vault URI"** and **"Resource ID"**

![](screenshots/13.Keyvault_props.jpg)

Go to Databricks create scope window

![](screenshots/14.DB_secrets_url.PNG)

Change **“Manage principal”** to **"All users"** if you use Trial or Standard subscription.  
In **“DNS Name”** paste **“Vault URI”** from Key Vault Properties.  
In **“Resource ID”** paste **“Resource ID”**. 

![](screenshots/15.DB_secrets.PNG)

Save the name of this scope (!)

### 3. Databricks

* Create cluster

![](screenshots/16.Databricks_cluster.PNG)

* Import **"Crypto.dbc"** to workspace

![](screenshots/17.Databricks_import_1.PNG)

![](screenshots/18.Databricks_import_2.PNG)

* Create Databricks job with notebook **"2.Api-to-EventHub"** and start it

![](screenshots/19.Databricks_job.PNG)

* We need a token to connect **Data Factory** to **Databricks**

Go to **“Settings”** - **“User settings”** - **“Generate new token”**  
Copy generated value(!) 

![](screenshots/20.Databricks_token.PNG)

### 4. Data Factory

* Open **"Azure Data Factory Studio"**

![](screenshots/21.ADF.PNG)

Create new pipeline and add 4 Databricks notebooks 
to it. Now we need to connect our Databricks workspace to ADF using token from 
previous step 

Click on first notebook created in ADF, go to **“Azure Databricks”** panel 
and click on “New” 

Choose your subscription, Databricks workspace, check 
**“Existing interactive cluster”**, set **“Authentication type”** to **“Access Token”**
and paste Databricks token to the next field. Choose the existing cluster in
the next field. Then click “Create” 

![](screenshots/22.ADF-Databricks.PNG)


Now connect this Databricks workspace to the other notebooks. 
Import notebooks number **1, 3, 4, 5** from your Databricks workspace
and connect them with green (**on success**) arrows in the same
order. Name them accordingly 

![](screenshots/23.Connect-notebooks.PNG)

Create trigger to run this pipeline every minute. Click **“Trigger”** - **“New/Edit”**. Create new trigger and schedule to it once a minute

![](screenshots/24.CryptoTrigger.PNG)

Now we need to create **“Copy Activity”** from **ADLS** Staged Area to **MongoDB Atlas**. Go to Data Factory home page and choose **“Ingest”** 

![](screenshots/25.ADF_Ingest.PNG)

Choose **“Built-in-copy-task”**. Check **“Tumbling window”** type, set **“Recurrence”** to **5 minutes** and click “Next” 

![](screenshots/26.Copy_Task.PNG)

Choose **“ADLS Gen 2”** as Source type and create new Connection with Account key Authentication 

![](screenshots/27.ADLS_Connection.PNG)

Set a path to data in staged area. Choose **“Incremental load: LastModifiedDate”** as **"File loading behaviour"**.  

![](screenshots/28.Silver-conect.PNG)

Choose **parquet** format, **snappy** compression 

![](screenshots/29.Silver-format.PNG)

Choose **MongoDB Atlas** as Destination data store, use your Mongo connection string and database name for connection. Check “Skip schema mapping” at the bottom of the page
![](screenshots/30.Mongo-ADF.PNG)

![](screenshots/31.Copy_created.PNG)

### 5. PowerBI  

* Open PowerBI Desktop
* Go to:
  * "Home" - "Get data" - "More" - search "Spark"

![](screenshots/32.PowerBI_Spark.PNG)

* Open Databricks in other window and go to "Compute" -> "Configuration" -> "JDBC/ODBC"
* Open any text editor and paste part of string from "JDBC URL" field from beginning to "443/" including
* Replace "jdbc:spark" to "https"
* Now add string from "Http Path" field to the end of URL
* Copy the result, it should look like this:
  * **https://\<workspace>.azuredatabricks.net:443/sql/protocolv1/o/\<n>/\<n>**
  
![](screenshots/33.Cluster_url.PNG)

* Paste this URL to "Server" field in PowerBI. Set "Protocol" to HTTP

![](screenshots/34.PowerBI_Spark.PNG)

* Choose table from Databricks and press "Load"

![](screenshots/36.BI_table.PNG)

* In this example I chose the "Line chart" model with crypto price timeline
  * "Axis" - **time**
  * "Legend" - **abbreviation**
  * "Values" - **last_price**

![](screenshots/37.report.PNG)

* Enable zoom slider to zoom on chart  
![](screenshots/38.scroll.PNG)

##Result:
  * ### Bitcoin chart

![](screenshots/39.Bitcoin.PNG)

  * ### Ethereum chart

![](screenshots/40.Ethereum.PNG)

  * ### Silver data

![](screenshots/41.Silver_data.PNG)

  * ### Gold data

![](screenshots/42.Gold_data.PNG)

  * ### MongoDB Atlas (Silver data)

![](screenshots/43.Mongo_result.PNG)

