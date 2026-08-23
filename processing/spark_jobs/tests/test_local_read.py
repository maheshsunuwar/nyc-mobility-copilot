from pyspark.sql import SparkSession

spark = SparkSession.builder.appName('LocalReadTest').getOrCreate()

df = spark.read.parquet('../../ingestion/batch/yellow_tripdata_2026-01.parquet')

print(f'Raw count: {df.count()}')
df.printSchema()

spark.stop()
