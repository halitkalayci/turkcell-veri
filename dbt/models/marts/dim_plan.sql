select
    plan_id,
    plan_name,
    plan_family,
    monthly_fee
from {{ ref('stg_plans') }}
where is_current_record = true

-- Doğrulama 1: Boyuttaki toplam plan sayısı.
-- select count(*) as total_rows
-- from gold.dim_plan;
--
-- Doğrulama 2: Plan anahtarının tekil olduğu kontrolü.
-- select count(*) as total_rows, count(distinct plan_id) as distinct_plan_id
-- from gold.dim_plan;
