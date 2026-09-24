with source as (
    select *
    from {{ source('raw', 'plans') }}
),
normalized as (
    select
        plan_id,
        trim(plan_name) as plan_name,
        trim(plan_family) as plan_family,
        monthly_fee
    from source
),
deduped as (
    select
        *,
        row_number() over (
            partition by plan_id
            order by plan_id desc
        ) as rn
    from normalized
)
select
    plan_id,
    plan_name,
    plan_family,
    monthly_fee,
    (rn = 1) as is_current_record
from deduped

-- Validation queries:
-- 1. Duplicate check before deduplication in the raw source:
-- select plan_id, count(*) as row_count
-- from raw.plans
-- where plan_id is not null
-- group by plan_id
-- having count(*) > 1;
--
-- 2. Final model: güncel kayıt sayısı ile distinct plan_id sayısının eşit olduğu kontrolü:
-- select count(*) as total_rows, count(distinct plan_id) as distinct_plan_id
-- from silver.stg_plans
-- where is_current_record = true;
