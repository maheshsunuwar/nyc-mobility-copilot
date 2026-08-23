from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName('S3ReadTest')
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.5.0")
    .getOrCreate()
)

print('SparkSession created successfully with hadoop-aws')
spark.stop()
