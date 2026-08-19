
for i in {1..5}; do
	echo "Downloading $i"
	curl -o "yellow_tripdata_2026-0$i.parquet" "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-0$i.parquet"

    echo "Save $i to s3"
    aws s3 cp "yellow_tripdata_2026-0$i.parquet" "s3://nyc-mobility-copilot-ms-15aug/raw/taxi/type=yellow/year=2026/month=0$i/yellow_tripdata_2026-0$i.parquet"
done
echo "Done."

for i in {1..5}; do
	echo "Downloading $i"
	curl -o "green_tripdata_2026-0$i.parquet" "https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2026-0$i.parquet"

    echo "Save $i to s3"
    aws s3 cp "green_tripdata_2026-0$i.parquet" "s3://nyc-mobility-copilot-ms-15aug/raw/taxi/type=green/year=2026/month=0$i/green_tripdata_2026-0$i.parquet"
done
echo "Done."
