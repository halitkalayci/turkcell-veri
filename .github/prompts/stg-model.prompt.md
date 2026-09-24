---
description: "raw tablo için dbt staging modeli + schema.yml testleri üret"
agent: dbt-stg-model-builder
---
`${input:table:raw tablo adı (örn. cdr_events)}` için dbt staging modeli oluştur.

Kalıp ve adımlar [dbt-stg-model SKILL.md](../skills/dbt-stg-model/SKILL.md) ve [dbt-staging.instructions.md](../instructions/dbt-staging.instructions.md) içinde tanımlıdır; onlara birebir uy.

Kısaca: `dbt/models/staging/sources.yml` + `stg_${input:table}.sql` + `schema.yml` üçlüsünü güncelle, modelin sonuna 2 doğrulama sorgusu ekle, `dbt run --select stg_${input:table}` ve `dbt test --select stg_${input:table}` çalıştır (repo kökünden `--project-dir dbt --profiles-dir dbt` ile).

Bitince: hangi varsayımları yaptığını ve instructions'a eklenmesi gereken yeni bir kural varsa öner.