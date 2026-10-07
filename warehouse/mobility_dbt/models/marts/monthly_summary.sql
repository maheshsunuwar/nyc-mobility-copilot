-- models/marts/montly_summary.sql
select
    taxi_type,
    year,
    month,
    sum(trip_count) as total_trips,
    avg(avg_fare) as avg_fare_across_zones
from {{ ref('stg_trips_by_hour_zone') }}
group by taxi_type, year, month
order by taxi_type, year, month
