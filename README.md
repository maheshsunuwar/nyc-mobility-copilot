## Repo Structure
```
nyc-mobility-copilot/
|--- infra/
|--- ingestion/
|   |--- batch/
|   |--- streaming/
|--- processing/
|   |--- spark_jobs/
|   |--- kafka_consumer/
|--- orchestration/
|   |--- airflow/dags/
|--- warehouse/
|   |---dbt/
|   |   |--- models/staging/
|   |   |--- models/intermediate/
|   |   |--- models/marts/
|--- ai agents/
|   |--- graph/
|   |--- api/
|--- frontend/
|--- README.md
```
## Infra

## Ingestion
It will do two different things.
1. batch ingestion
2. streaming ingestion
Batch ingestion is for the NY TLC trip data. And streaming is for the city bike nyc data.

For the batch, we need to run the `download_and_upload_to_s3.bash` file. It will do exactly what the file name says it does.
