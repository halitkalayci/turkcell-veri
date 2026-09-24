---
name: dbt-stg-model
description: 'Use when building or fixing a dbt staging model (stg_*) for a raw telco table (sources.yml + stg_<table>.sql + schema.yml triad). Applies the canonical stg_subscribers normalization/dedup/testing pattern: msisdn E.164, ROW_NUMBER dedup, is_valid_* flags, accepted_values/unique/not_null tests, trailing validation queries.'
argument-hint: 'raw tablo adı (örn. cdr_events)'
---

# dbt Staging Model Oluşturma

Kalıbın tam kuralları [dbt-staging.instructions.md](../../instructions/dbt-staging.instructions.md) içinde tanımlıdır; bu dosya o kuralları uygularken izlenecek adım adım iş akışıdır. Şema gerçekleri (msisdn formatı, dedup zorunluluğu, status/event_type varyantları) için [copilot-instructions.md](../../copilot-instructions.md)'e bak.

## Ne Zaman Kullanılır

- Yeni bir `raw.<table>` için `stg_<table>` modeli oluşturulacağında.
- Var olan bir staging modelinin normalize/dedup/test mantığı gözden geçirilecek ya da onarılacağında.

## Adımlar

1. **Kaynağı incele**: hedef raw tablonun kolonlarını ve bilinen kirlilik noktalarını (varyant statü, karışık msisdn formatı, tekrarlanan anahtar vb.) belirle. Emin olunamayan bir şema/iş kuralı varsa varsayım yapmadan `vscode_askQuestions` ile sor.
2. **sources.yml**: `dbt/models/staging/sources.yml`'de tablo yoksa ekle; tablo ve kolon açıklamaları yaz.
3. **stg_<table>.sql**: [şablonu](./assets/stg_model_template.sql) başlangıç noktası olarak kullan; `source → normalized → deduped → final select` CTE zincirini instructions dosyasındaki kurallara göre doldur.
4. **schema.yml**: Model + kolon açıklamaları, doğal anahtara `unique`+`not_null`, varyant kolonlara `is_valid_*` şartlı `accepted_values`/`not_null` testleri ekle.
5. **Doğrulama sorguları**: Model dosyasının sonuna tam 2 doğrulama sorgusu yorum olarak ekle (dedup öncesi tekrar sayımı, dedup sonrası distinct kontrolü).
6. **Çalıştır ve doğrula**: repo kökünden
   ```
   dbt run --select stg_<table> --project-dir dbt --profiles-dir dbt
   dbt test --select stg_<table> --project-dir dbt --profiles-dir dbt
   ```
   çalıştır, sonucu özetle. Test başarısızsa kalıbı değil veriyi/normalizasyonu sorgula, testi gevşetmeden önce nedenini açıkla.
7. **Kapanış**: Hangi varsayımların yapıldığını ve instructions/copilot-instructions.md'ye eklenmesi gereken yeni bir şema gerçeği varsa öner.

## Referans Model

[stg_subscribers.sql](../../../dbt/models/staging/stg_subscribers.sql), [schema.yml](../../../dbt/models/staging/schema.yml) ve [sources.yml](../../../dbt/models/staging/sources.yml) bu kalıbın canlı örneğidir; yeni bir modelde şüpheye düşülürse bunlara bakılır.
