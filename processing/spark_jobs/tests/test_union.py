from pyspark.sql import SparkSession
from pyspark.sql.functions import lit # lets us inject a constant value into a new column

spark = SparkSession.builder.appName('UnionTest').getOrCreate()

yellow = spark.read.parquet("../../ingestion/batch/yellow_tripdata_2026-01.parquet")
green = spark.read.parquet("../../ingestion/batch/green_tripdata_2026-01.parquet")

yellow_std = (
    yellow
        .withColumnRenamed('tpep_pickup_datetime', "pickup_datetime")
        .withColumnRenamed("tpep_dropoff_datetime", "dropoff_datetime")
        .withColumn("taxi_type", lit('yellow'))
)

green_std = (
    green
        .withColumnRenamed('lpep_pickup_datetime', "pickup_datetime")
        .withColumnRenamed("lpep_dropoff_datetime", "dropoff_datetime")
        .withColumn("taxi_type", lit('green'))
)

combined = yellow_std.unionByName(green_std, allowMissingColumns=True)

print(f"Yellow count: {yellow_std.count()}")
print(f"Green count: {green_std.count()}")
print(f"Combined count: {combined.count()}")

combined.groupBy('taxi_type').count().show()

combined.select("taxi_type", "pickup_datetime", "dropoff_datetime", "trip_distance").show(5)

combined.filter("taxi_type=='green'").show(5)
combined.filter(combined.taxi_type == "green").show(5)
