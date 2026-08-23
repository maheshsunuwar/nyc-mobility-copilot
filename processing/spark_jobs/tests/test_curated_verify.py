from pyspark.sql import SparkSession
import boto3

session = boto3.Session()
creds = session.get_credentials()

spark = (
    SparkSession.builder
    .appName("VerifyCurated")
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.5.0")
    .config("spark.hadoop.fs.s3a.access.key", creds.access_key)
    .config("spark.hadoop.fs.s3a.secret.key", creds.secret_key)
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    .getOrCreate()
)

curated = spark.read.parquet("s3a://nyc-mobility-copilot-ms-15aug/curated/taxi_trips/")

print(f"Curated columns: {curated.columns}")
print(f"Curated total rows: {curated.count()}")
curated.groupBy("taxi_type", "month").count().orderBy("taxi_type", "month").show(20)

spark.stop()
