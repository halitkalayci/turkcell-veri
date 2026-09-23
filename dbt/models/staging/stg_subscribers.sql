with source as (
    select *
    from {{ source('raw', 'subscribers') }}
),
normalized as (
    select
        subscriber_id,
        trim(msisdn) as msisdn_raw,
        case
            when msisdn is null or trim(msisdn) = '' then null
            else '+' || right(regexp_replace(trim(msisdn), '\D', '', 'g'), 10)
        end as msisdn,
        plan_id,
        case
            when status is null or trim(status) = '' then null
            when upper(trim(status)) in ('ACTIVE', 'AKTIF') then 'ACTIVE'
            when upper(trim(status)) in ('SUSPENDED', 'INACTIVE', 'PASSIVE', 'CHURNED', 'CHURN', 'INACTIF') then 'INACTIVE'
            else null
        end as status_normalized,
        case
            when status is null or trim(status) = '' then false
            when upper(trim(status)) in ('ACTIVE', 'AKTIF', 'SUSPENDED', 'INACTIVE', 'PASSIVE', 'CHURNED', 'CHURN', 'INACTIF') then true
            else false
        end as is_valid_status,
        activation_date,
        city,
        segment
    from source
),
deduped as (
    select
        *,
        row_number() over (
            partition by msisdn
            order by activation_date desc, subscriber_id desc
        ) as rn
    from normalized
)
select
    subscriber_id,
    msisdn,
    plan_id,
    status_normalized as status,
    is_valid_status,
    activation_date,
    city,
    segment
from deduped
where rn = 1

-- Validation queries:
-- 1. Duplicate check before deduplication in the raw source:
-- select msisdn, count(*) as row_count
-- from raw.subscribers
-- where msisdn is not null
-- group by msisdn
-- having count(*) > 1;
--
-- 2. Final model uniqueness check by normalized MSISDN:
-- select count(*) as total_rows, count(distinct msisdn) as distinct_msisdn
-- from silver.stg_subscribers;
