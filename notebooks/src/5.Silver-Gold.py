# Databricks notebook source
# MAGIC %run ./Includes/Configuration

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE DATABASE IF NOT EXISTS crypto;
# MAGIC USE crypto;

# COMMAND ----------

spark.conf.set("spark.sql.shuffle.partitions", 8)

# COMMAND ----------

from pyspark.sql.functions import *

temp_aggregate_stream = (
    spark
    .readStream
    .format("delta")
    .option("ignoreChanges", "true")
    .load(gold_temp)
)

# COMMAND ----------

result_gold_stream = (
    temp_aggregate_stream.alias("g1")
    .join(
        temp_aggregate_stream.alias("g2"), 
            (col("g1.abbreviation") == col("g2.abbreviation")) & 
            (col("g2.window_start") == col("g1.window_start") + expr('INTERVAL 1 second')) & 
            (col("g2.window_end") == col("g1.window_end") + expr('INTERVAL 1 second'))
    )
    .select(
        col("g1.abbreviation"),
        col("g2.window_start").alias("time"),
        col("g2.year"),
        col("g2.month"),
        col("g2.day"),
        col("g2.hour"),
        col("g2.minute"),
        second(col("g2.window_start")).alias("second"),
        col("g2.price_changes_count"),
        col("g2.last_price"),
        round((col("g2.last_price") - col("g1.last_price")), 4).alias("change"),
        round(((col("g2.last_price") - col("g1.last_price")) / col("g2.last_price") * 100), 4).alias("%_change")
    )
)

# COMMAND ----------

def process_to_bi_with_adls(source_df, batch_id):
    source_df.cache()
    (
        source_df
         .write
         .format("delta")
         .partitionBy("year", "month", "day", "hour", "minute", "second")
         .mode("append")
         .save(gold_output)
    )
    (
    source_df
        .write
        .mode("append")
        .saveAsTable("crypto_currency")
    )
    source_df.unpersist()

# COMMAND ----------

(
    result_gold_stream
        .coalesce(1)
        .writeStream
        .option("checkpointLocation", gold_check)
        .trigger(once=True)
        .foreachBatch(process_to_bi_with_adls)
        .start()
)