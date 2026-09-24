with source as (
    select *
    from {{ source('raw', 'recharges') }}
),
normalized as (
    select
        recharge_id,
        case
            when msisdn is null or trim(msisdn) = '' then null
            else '+90' || right(regexp_replace(trim(msisdn), '\D', '', 'g'), 10)
        end as msisdn,
        amount_try,
        upper(trim(channel)) as channel,
        recharge_ts
    from source
),
deduped as (
    select
        *,
        row_number() over (
            partition by recharge_id
            order by recharge_ts desc, recharge_id desc
        ) as rn
    from normalized
)
select
    recharge_id,
    msisdn,
    amount_try,
    channel,
    recharge_ts,
    (rn = 1) as is_current_record
from deduped

-- Validation queries:
-- 1. Duplicate check before deduplication in the raw source:
-- select recharge_id, count(*) as row_count
-- from raw.recharges
-- where recharge_id is not null
-- group by recharge_id
-- having count(*) > 1;
--
-- 2. Final model: güncel kayıt sayısı ile distinct recharge_id sayısının eşit olduğu kontrolü:
-- select count(*) as total_rows, count(distinct recharge_id) as distinct_recharge_id
-- from silver.stg_recharges
-- where is_current_record = true;
