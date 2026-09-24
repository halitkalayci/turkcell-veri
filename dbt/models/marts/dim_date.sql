with date_spine as (
    select cast(date_day as date) as date_day
    from generate_series(
        date '2026-01-01',
        date '2027-12-31',
        interval '1 day'
    ) as generated_dates(date_day)
)
select
    date_day,
    extract(isodow from date_day)::integer as iso_weekday,
    extract(isodow from date_day)::integer in (6, 7) as is_weekend,
    strftime(date_day, '%Y-%m') as year_month
from date_spine

-- Doğrulama 1: Tarih boyutunun kapsayıcı aralık ve satır sayısı kontrolü.
-- select min(date_day) as min_date_day, max(date_day) as max_date_day, count(*) as total_rows
-- from gold.dim_date;
--
-- Doğrulama 2: Tarih anahtarının tekil olduğu kontrolü.
-- select count(*) as total_rows, count(distinct date_day) as distinct_date_day
-- from gold.dim_date;
