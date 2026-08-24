from pyspark.sql import SparkSession
import boto3

session = boto3.Session()
creds = session.get_credentials()

spark = (
    SparkSession.builder
    .appName("FileReader")
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.5.0")
    .config("spark.hadoop.fs.s3a.access.key", creds.access_key)
    .config("spark.hadoop.fs.s3a.secret.key", creds.secret_key)
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    .getOrCreate()
)

BUCKET = 'nyc-mobility-copilot-ms-15aug'
trips_by_hour_zone = spark.read.parquet(f"s3a://{BUCKET}/marts/trips_by_hour_zone/")
trips_by_hour_zone.orderBy("pickup_hour").show(10)

spark.stop()
