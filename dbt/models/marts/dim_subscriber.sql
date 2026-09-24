select
    {{ dbt_utils.generate_surrogate_key(['msisdn', 'dbt_valid_from']) }} as subscriber_sk,
    msisdn,
    plan_id,
    status,
    segment,
    city,
    dbt_valid_from as valid_from,
    dbt_valid_to as valid_to,
    (dbt_valid_to is null) as is_current
from {{ ref('snap_subscriber_plan') }}

-- Doğrulama 1: Boyuttaki toplam satır sayısı.
-- select count(*) as total_rows
-- from gold.dim_subscriber;
--
-- Doğrulama 2: Surrogate anahtarın tekil olduğu kontrolü.
-- select count(*) as total_rows, count(distinct subscriber_sk) as distinct_subscriber_sk
-- from gold.dim_subscriber;