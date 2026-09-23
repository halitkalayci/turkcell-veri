# DuckDB Kopyası

PostgreSQL dosyalarına dokunmadan DuckDB kopyasını oluşturmak için repo kökünde çalıştırın:

```powershell
python -m pip install -r requirements.txt
python load_duckdb.py --replace
```

Çıktı `duckdb/telco_dw.duckdb` dosyasıdır. PostgreSQL şema adları tek dosyada korunur: `raw`, `silver`, `gold`, `quarantine` ve `audit`.

DuckDB istemcisiyle bağlanma:

```powershell
duckdb duckdb/telco_dw.duckdb
```

Doğrulama sorguları:

```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'raw'
ORDER BY table_name;

SELECT 'subscribers' AS table_name, COUNT(*) AS row_count FROM raw.subscribers
UNION ALL SELECT 'cdr_events', COUNT(*) FROM raw.cdr_events
UNION ALL SELECT 'recharges', COUNT(*) FROM raw.recharges
UNION ALL SELECT 'plan_changes', COUNT(*) FROM raw.plan_changes;
```