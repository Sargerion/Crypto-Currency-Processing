# Databricks notebook source
# MAGIC %run ./Includes/Configuration

# COMMAND ----------

spark.conf.set("spark.sql.shuffle.partitions", 8)

# COMMAND ----------

from pyspark.sql.types import *
from pyspark.sql.functions import *

body_schema = StructType([
    StructField("body", BinaryType(), True)
])

stock_df = (
  spark 
    .readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "avro")
    .schema(body_schema)
    .load("/mnt/bronze-crypto/crypto-eventhub201/*")
)

# COMMAND ----------

stock_schema = StructType([
  StructField("data", ArrayType(
      StructType([
          StructField("p", DoubleType(), True),
          StructField("s", StringType(), True),
          StructField("t", StringType(), True)
      ])
   ), True)
])

raw_event = (
    stock_df
    .select(
        from_json(col("body").cast("string"), stock_schema).alias("body")
    )
)

# COMMAND ----------

flat_schema_stock = (
    raw_event
    .select(
        explode("body.data").alias("data")
    )
    .select(
        col("data.p").alias("current_price"),
        col("data.s").alias("abbreviation"),
        col("data.t").cast("long").alias("initial_time"),
        to_utc_timestamp(
            concat_ws(".", from_unixtime((col("data.t") / 1000), "yyyy-MM-dd HH:mm:ss"), substring(col("data.t"), -3, 3)), "UTC-3"
        ).alias("date")
    )
    .withColumn("year", year(col("date")))
    .withColumn("month", month(col("date")))
    .withColumn("day", dayofmonth(col("date")))
    .withColumn("hour", hour(col("date")))
    .withColumn("minute", minute(col("date")))
    .withColumn("second", second(col("date")))
    .withColumn("millisecond", (col("initial_time") % 1000).cast("int"))
    .dropDuplicates()
)

# COMMAND ----------

silver_df = (
    flat_schema_stock
    .select(
        col("current_price"),
        col("abbreviation"),
        col("date"),
        col("year"),
        col("month"),
        col("day"),
        col("hour"),
        col("minute"),
        col("second")
        col("millisecond")
      )
)

# COMMAND ----------

(
    silver_df
    .coalesce(1)
    .writeStream
    .partitionBy("year", "month", "day", "hour", "minute", "second")
    .format("delta")
    .option("checkpointLocation", silver_check)
    .trigger(once=True)
    .start(silver_output)
)