# Databricks notebook source
dbutils.fs.mkdirs(gold_check)
dbutils.fs.mkdirs(gold_temp)
dbutils.fs.mkdirs(silver_check)
dbutils.fs.mkdirs(gold_check_temp)
dbutils.fs.mkdirs(gold_output)
dbutils.fs.mkdirs(silver_output)