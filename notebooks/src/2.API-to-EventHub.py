# Databricks notebook source
# MAGIC %md
# MAGIC ## ![Spark Logo Tiny](https://files.training.databricks.com/images/105/logo_spark_tiny.png) Install packages for FinnHub API and EventHub

# COMMAND ----------

# MAGIC %pip install websocket
# MAGIC %pip install websocket-client
# MAGIC %pip install azure-eventhub

# COMMAND ----------

REQUEST_MESSAGE = '{{ "type":"subscribe", "symbol":"BINANCE:{}" }}'
BITCOIN_CODE = "BTCUSDT"
ETHERIUM_CODE = "ETHUSDT"
TOKEN="c69tao2ad3idi8g5j3c0"

EVENT_HUB_CONNECTION = dbutils.secrets.get(scope = "crypto-db-scope", key = "eventhub-connstr")
EVENT_HUB_NAME = "crypto201"

# COMMAND ----------

import websocket
from azure.eventhub import EventHubProducerClient, EventData
from azure.eventhub.exceptions import EventHubError

def on_message(ws, message):
    try:
        producer = EventHubProducerClient.from_connection_string(
            conn_str=EVENT_HUB_CONNECTION,
            eventhub_name=EVENT_HUB_NAME
        )
        with producer:
            producer.send_batch([EventData(message)])
    except EventHubError as eh_err:
        print("EventHub error: ", eh_err)


def on_open(ws):
    ws.send(REQUEST_MESSAGE.format(BITCOIN_CODE)) # Bitcoin
    ws.send(REQUEST_MESSAGE.format(ETHERIUM_CODE)) # Etherium

# COMMAND ----------

websocket.enableTrace(True)
ws = websocket.WebSocketApp(
    "wss://ws.finnhub.io?token={}".format(TOKEN),
    on_open=on_open,
    on_message=on_message
)
ws.run_forever()