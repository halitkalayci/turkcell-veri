with source as (
    select *
    from {{ source('raw', 'cdr_events') }}
),
normalized as (
    select
        event_id,
        case
            when msisdn is null or trim(msisdn) = '' then null
            else '+90' || right(regexp_replace(trim(msisdn), '\D', '', 'g'), 10)
        end as msisdn,
        case
            when event_type is null or trim(event_type) = '' then null
            when lower(trim(event_type)) in ('voice', 'sms', 'data') then lower(trim(event_type))
            else null
        end as event_type,
        case
            when event_type is null or trim(event_type) = '' then false
            when lower(trim(event_type)) in ('voice', 'sms', 'data') then true
            else false
        end as is_valid_event_type,
        event_ts,
        duration_sec,
        bytes,
        cell_id,
        country_code,
        ingested_at
    from source
),
deduped as (
    select
        *,
        row_number() over (
            partition by event_id
            order by ingested_at, event_ts, event_id
        ) as rn
    from normalized
)
select
    event_id,
    msisdn,
    event_type,
    is_valid_event_type,
    event_ts,
    duration_sec,
    bytes,
    cell_id,
    country_code,
    ingested_at
from deduped
where rn = 1

-- Validation queries:
-- 1. Duplicate check before deduplication in the raw source:
-- select event_id, count(*) as row_count
-- from raw.cdr_events
-- where event_id is not null
-- group by event_id
-- having count(*) > 1;
--
-- 2. Final model uniqueness check by event ID:
-- select count(*) as total_rows, count(distinct event_id) as distinct_event_id
-- from silver.stg_cdr_events;