# Databricks notebook source
storage="stcrypto201westeurope"

bronze="bronze-crypto"
silver="silver-crypto"
gold="gold-crypto"

bronze_mount="/mnt/bronze-crypto"
silver_mount="/mnt/silver-crypto"
gold_mount="/mnt/gold-crypto"

silver_check="/mnt/silver-crypto/check"
gold_check_temp="/mnt/gold-crypto/check_temp"
gold_check="/mnt/gold-crypto/check"

silver_output="/mnt/silver-crypto/data"
gold_temp="/mnt/gold-crypto/temp"
gold_output="/mnt/gold-crypto/data"