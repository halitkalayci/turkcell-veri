{% snapshot snap_subscriber_plan %}

{{
    config(
        target_schema='snapshots',
        unique_key='msisdn',
        strategy='check',
        check_cols=['plan_id', 'status', 'segment', 'city']
    )
}}

select
    msisdn,
    plan_id,
    status,
    segment,
    city
from {{ ref('stg_subscribers') }}
where is_current_record = true

{% endsnapshot %}