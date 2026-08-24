from pyspark.sql import SparkSession
import boto3

def get_s3_spark_session(app_name: str) -> SparkSession:
    """Returns a Spark Session for s3 with given app name.
    """
    session = boto3.Session()
    creds = session.get_credentials()
    spark = (
        SparkSession.builder
        .appName("")
        .config("spark.jars.packages","org.apache.hadoop:hadoop-aws:3.5.0")
        .config("spark.hadoop.fs.s3a.access.key", creds.access_key)
        .config("spark.hadoop.fs.s3a.secret.key", creds.secret_key)
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        .getOrCreate()
    )

    return spark
