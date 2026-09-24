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
            else '+90' || right(regexp_replace(msisdn, '\D', '', 'g'), 10)
        end as msisdn,
        plan_id,
        case
            when status is null or trim(status) = '' then null
            when upper(trim(status)) in ('ACTIVE', 'AKTIF') then 'ACTIVE'
            else upper(trim(status))
        end as status_normalized,
        case
            when status is null or trim(status) = '' then false
            else true
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
    segment,
    (rn = 1) as is_current_record
from deduped

-- Validation queries:
-- 1. Duplicate check before deduplication in the raw source:
-- select msisdn, count(*) as row_count
-- from raw.subscribers
-- where msisdn is not null
-- group by msisdn
-- having count(*) > 1;
--
-- 2. Final model: güncel kayıt sayısı (msisdn, subscriber_id) ile distinct kombinasyon sayısı eşleşmeli:
-- select count(*) as total_rows, count(distinct (msisdn, subscriber_id)) as distinct_combo
-- from silver.stg_subscribers
-- where is_current_record = true;
