-- İskelet: <table> yerine hedef raw tablo adını, <key> yerine doğal anahtarı yaz.
with source as (
    select *
    from {{ source('raw', '<table>') }}
),
normalized as (
    select
        <id_column>,
        -- msisdn varsa E.164 normalizasyonu:
        case
            when msisdn is null or trim(msisdn) = '' then null
            else '+' || right(regexp_replace(trim(msisdn), '\D', '', 'g'), 10)
        end as msisdn,
        -- varyantlı bir kolon örneği (status/event_type vb.):
        case
            when <variant_column> is null or trim(<variant_column>) = '' then null
            when upper(trim(<variant_column>)) in (/* geçerli varyantlar */) then '<NORMALIZED_VALUE>'
            else null
        end as <variant_column>_normalized,
        case
            when <variant_column> is null or trim(<variant_column>) = '' then false
            when upper(trim(<variant_column>)) in (/* bilinen tüm varyantlar */) then true
            else false
        end as is_valid_<variant_column>
        -- diğer geçirilecek kolonlar...
    from source
),
deduped as (
    select
        *,
        row_number() over (
            partition by <key>
            order by <tie_break_desc_column> desc, <id_column> desc
        ) as rn
    from normalized
)
select
    <id_column>,
    msisdn,
    <variant_column>_normalized as <variant_column>,
    is_valid_<variant_column>
    -- diğer kolonlar...
from deduped
where rn = 1

-- Validation queries:
-- 1. Dedup öncesi doğal anahtarda tekrar sayımı:
-- select <key>, count(*) as row_count
-- from raw.<table>
-- where <key> is not null
-- group by <key>
-- having count(*) > 1;
--
-- 2. Dedup sonrası tekillik kontrolü:
-- select count(*) as total_rows, count(distinct <key>) as distinct_key
-- from silver.stg_<table>;
