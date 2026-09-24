---
description: "Use when creating or editing dbt staging models (stg_*) under dbt/models/staging: sources.yml entries, stg_<table>.sql normalization/dedup logic, and schema.yml tests."
applyTo: "dbt/models/staging/**"
---

# Staging Model Kalıbı (stg_subscribers referans alınır)

Her staging modeli şu üç dosyayı birlikte günceller: `sources.yml` (kaynak tanımı), `stg_<table>.sql` (dönüşüm), `schema.yml` (doküman + test). Üçü de eksiksiz olmadan model tamamlanmış sayılmaz.

## sources.yml

- `sources: - name: raw` altına yeni tablo girilir; tablo ve her kolon için kısa `description` yazılır.
- Kaynakta `ingested_at` varsa ve freshness kontrolü isteniyorsa `loaded_at_field: ingested_at` eklenir.

## stg_<table>.sql — CTE sırası

Sabit CTE zinciri kullanılır, isimler değişmez:

1. `source` — `select * from {{ source('raw', '<table>') }}`.
2. `normalized` — copilot-instructions.md'deki şema gerçekleri burada uygulanır:
   - `msisdn`: `'+' || right(regexp_replace(trim(msisdn), '\D', '', 'g'), 10)`, boş/null için `null`.
   - Varyantlı metin kolonları (`status`, `event_type` vb.): `upper(trim(...))` ile normalize edilip sabit bir değer kümesine eşlenir; eşlenemeyen değerler `null` yapılır ama satır silinmez.
   - Her varyantlı kolon için ayrı bir `is_valid_<kolon>` boolean kolonu üretilir (geçersiz görülen satırları işaretlemek için — silmek için değil).
3. `deduped` — `row_number() over (partition by <doğal anahtar> order by <en güncel kaydı öne alan tie-break kolonları> desc, <id> desc) as rn`. Doğal anahtar iş tanımına göre değişir (ör. `msisdn`, ya da `event_id`).
4. Son `select` — `deduped`'den `rn = 1` filtresiyle, gereksiz/ham kolonlar (`*_raw`, `rn`) dışarıda bırakılır.

Ayrı bir "final" CTE'ye gerek yok; son `select` doğrudan `deduped` üzerinden yazılır.

## schema.yml testleri

- Model açıklaması ve her kolon için `description` zorunludur.
- Doğal anahtar kolonuna `unique` + `not_null`.
- Kaynaktan gelen kimlik kolonlarına (`subscriber_id`, `event_id` vb.) `not_null`.
- Normalize edilmiş varyant kolonlara (`status` vb.) `accepted_values` ve `not_null`; ikisi de yalnızca geçerli satırlarda çalışacak şekilde `config: where: "is_valid_<kolon> = true"` ile sınırlanır.
- `is_valid_<kolon>` kolonunun kendisine `not_null` (bu kolon hiçbir zaman null olmaz, geçerlilik `true/false` ile ifade edilir).

## Doğrulama sorguları

Model dosyasının sonuna yorum satırı olarak tam 2 doğrulama sorgusu eklenir:
1. Dedup öncesi doğal anahtarda kaç tekrar var (kaynak tablo üzerinde `group by ... having count(*) > 1`).
2. Dedup sonrası toplam satır sayısı ile distinct doğal anahtar sayısının eşit olduğu kontrolü.

## Yol notu

Model dosyaları `dbt/models/staging/` altındadır (proje adı `telco_dw` yalnızca `target/compiled` ve `target/run` altındaki derlenmiş çıktı yollarında görünür — kaynak model yolunda kullanılmaz).
