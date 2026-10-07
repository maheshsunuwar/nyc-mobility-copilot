from spark_session import get_s3_spark_session

BUCKET = 'nyc-mobility-copilot-ms-15aug'
spark  = get_s3_spark_session("LoadMartsToPostgres")

try:
    marts = spark.read.parquet(f"s3a://{BUCKET}/marts/trips_by_hour_zone/")
    marts_renamed = marts.withColumnRenamed("PULocationID", "pickup_location_id")

    (
        marts_renamed
        .write
        .format("jdbc")
        .option("url", "jdbc:postgresql://localhost:5432/mobility_warehouse")
        .option("dbtable", "trips_by_hour_zone")
        .option("user", "mobility")
        .option("password", "mobility_dev_pw")
        .option("driver", "org.postgresql.Driver")
        .option("truncate", "true")
        .mode("overwrite")
        .save()
    )

    print("Loaded marts data into Postgres")
finally:
    spark.stop()
