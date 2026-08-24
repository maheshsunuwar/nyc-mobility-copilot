from pyspark.sql.functions import avg, count, hour
from spark_session import get_s3_spark_session


BUCKET = "nyc-mobility-copilot-ms-15aug"

spark = get_s3_spark_session("BuildMartsHourly")

try:
    curated = spark.read.parquet(f"s3a://{BUCKET}/curated/taxi_trips/")

    hourly = (
        curated
        .withColumn("pickup_hour", hour("pickup_datetime"))
        .groupBy("taxi_type", "PULocationID", "year", "month", "pickup_hour")
        .agg(
            count("*").alias("trip_count"),
            avg("fare_amount").alias("avg_fare")
        )
    )
    print(f"Mart row count (should be far less than 19.2M): {hourly.count()}")
    # print(f"{hourly.show(10)}")

    hourly.orderBy("trip_count", ascending=False).show(10)
    (
        hourly
        .coalesce(1)
        .write
        .mode('overwrite')
        .partitionBy("taxi_type", "year", "month")
        .parquet(f"s3a://{BUCKET}/marts/trips_by_hour_zone/")
    )

    print("Mart written successfully")
finally:
    spark.stop()
