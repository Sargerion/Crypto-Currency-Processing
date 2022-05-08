# Databricks notebook source
# MAGIC %run ./Includes/Configuration

# COMMAND ----------

spark.conf.set("spark.sql.shuffle.partitions", 8)

# COMMAND ----------

from pyspark.sql.functions import *

silver_df = (
    spark
    .readStream
    .format("delta")
    .load(silver_output)
)

# COMMAND ----------

temporary_gold_df = (
    silver_df
    .groupBy(
        "abbreviation",
        "year",
        "month",
        "day",
        "hour",
        "minute",
        window("date", "1 second", "1 second")
    )
    .agg(
        approx_count_distinct(col("current_price")).alias("price_changes_count"),
        last(col("current_price")).alias("last_price")
    )
    .withColumn("window_start", to_timestamp(col("window.start")))
    .withColumn("window_end", to_timestamp(col("window.end")))
    .select(
        col("abbreviation"),
        col("year"),
        col("month"),
        col("day"),
        col("hour"),
        col("minute"),
        second(col("window_start")).alias("second"),
        col("last_price"),
        col("price_changes_count"),
        col("window_start"),
        col("window_end")
    )
)

# COMMAND ----------

(
    temporary_gold_df
    .coalesce(1)
    .writeStream
    .partitionBy("year", "month", "day", "hour", "minute", "second")
    .option("checkpointLocation", gold_check_temp)
    .format("delta")
    .outputMode("complete")
    .trigger(once=True)
    .start(gold_temp)
)