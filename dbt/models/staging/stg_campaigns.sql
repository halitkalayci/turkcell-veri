with source as (
    select *
    from {{ source('raw', 'campaigns') }}
),
normalized as (
    select
        trim(campaign_id) as campaign_id,
        trim(name) as name,
        start_date,
        end_date,
        trim(target_segment) as target_segment
    from source
),
deduped as (
    select
        *,
        row_number() over (
            partition by campaign_id
            order by start_date desc, end_date desc, name desc, target_segment desc, campaign_id desc
        ) as rn
    from normalized
)
select
    campaign_id,
    name,
    start_date,
    end_date,
    target_segment
from deduped
where rn = 1

-- Doğrulama sorguları:
-- 1. Tekilleştirme öncesi ham kaynakta tekrar kontrolü:
-- select campaign_id, count(*) as row_count
-- from raw.campaigns
-- where campaign_id is not null
-- group by campaign_id
-- having count(*) > 1;
--
-- 2. Son modelde kampanya kimliği tekillik kontrolü:
-- select count(*) as total_rows, count(distinct campaign_id) as distinct_campaign_id
-- from silver.stg_campaigns;