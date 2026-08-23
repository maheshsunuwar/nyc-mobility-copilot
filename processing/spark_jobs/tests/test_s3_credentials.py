from pyspark.sql import SparkSession
import boto3

# reuse the same credentials that the aws cli has configured already instead of hardcoding
session = boto3.Session()
creds = session.get_credentials()

spark = (
    SparkSession.builder
    .appName('S3CredentialsTest')
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.5.0")
    .config("spark.hadoop.fs.s3a.access.key", creds.access_key)
    .config("spark.hadoop.fs.s3a.secret.key", creds.secret_key)
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    .getOrCreate()
)

df = spark.read.parquet("s3a://nyc-mobility-copilot-ms-15aug/raw/taxi/type=yellow/year=2026/month=01/")
print(f"Row count from S3: {df.count()}")

spark.stop()
