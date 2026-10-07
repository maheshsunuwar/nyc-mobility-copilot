-- models/staging/stg_trips_by_hour_zone.sql
select
    taxi_type,
    pickup_location_id,
    year,
    month,
    pickup_hour,
    trip_count,
    avg_fare
from {{ source('mobility_warehouse', 'trips_by_hour_zone') }}
