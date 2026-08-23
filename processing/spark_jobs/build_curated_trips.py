from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
import boto3

session = boto3.Session()
creds = session.get_credentials()

spark = (
    SparkSession.builder
    .appName("BuildCuratedTrips")
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.5.0")
    .config("spark.hadoop.fs.s3a.access.key", creds.access_key)
    .config("spark.hadoop.fs.s3a.secret.key", creds.secret_key)
    .config("spark.hadoop.fs.s3a.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSProvider")
    .getOrCreate()
)

BUCKET = 'nyc-mobility-copilot-ms-15aug'

# one wildcard read per type (month=*). lets Spark discover al 5 months at once
# and year/month become rea columns automatically fromt he folder structure
yellow = spark.read.parquet(f"s3a://{BUCKET}/raw/taxi/type=yellow/")
green = spark.read.parquet(f"s3a://{BUCKET}/raw/taxi/type=green/")

print(f"Yellow columns include partition columns: {yellow.columns}")
print(f"Yellow total rows across all months: {yellow.count()}")
print(f"Green total rows across all months: {green.count()}")

# Same rename/tag logic as before -- now applied across all 5 months at once
yellow_std = (
    yellow
    .withColumnRenamed("tpep_pickup_datetime", "pickup_datetime")
    .withColumnRenamed("tpep_dropoff_datetime", "dropoff_datetime")
    .withColumn("taxi_type", lit("yellow"))
)

green_std = (
    green
    .withColumnRenamed("lpep_pickup_datetime", "pickup_datetime")
    .withColumnRenamed("lpep_dropoff_datetime", "dropoff_datetime")
    .withColumn("taxi_type", lit("green"))
)

combined = yellow_std.unionByName(green_std, allowMissingColumns=True)
print(f"Combined total rows: {combined.count()}")
print(combined.columns)
(
    combined
    .groupBy("taxi_type", "month")
    .count()
    .orderBy("taxi_type", "month")
    .show(20)
)

OUTPUT_PATH = f"s3a://{BUCKET}/curated/taxi_trips/"

(
    combined
    .coalesce(1)                          # one clean file per folder, not several fragments
    .write
    .mode("overwrite")                    # always rebuild fresh -- no duplicate rows across reruns
    .partitionBy("taxi_type", "year", "month")    # creates taxi_type=X/month=Y/ folders, same trick as the read
    .parquet(OUTPUT_PATH)
)

spark.stop()
