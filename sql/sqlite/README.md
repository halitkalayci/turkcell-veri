# SQLite Kopyası

PostgreSQL dosyalarına dokunmadan SQLite kopyasını oluşturmak için repo kökünde çalıştırın:

```powershell
python load_sqlite.py --replace
```

Çıktı `sqlite/` dizinindedir. PostgreSQL şemaları, ayrı SQLite veritabanları olarak korunur: `raw.sqlite`, `silver.sqlite`, `gold.sqlite`, `quarantine.sqlite` ve `audit.sqlite`. `telco_dw.sqlite` bağlanmak için kullanılan ana dosyadır.

Sorgudan önce şemaları bağlayın:

```sql
ATTACH DATABASE 'sqlite/raw.sqlite' AS raw;
ATTACH DATABASE 'sqlite/silver.sqlite' AS silver;
ATTACH DATABASE 'sqlite/gold.sqlite' AS gold;
ATTACH DATABASE 'sqlite/quarantine.sqlite' AS quarantine;
ATTACH DATABASE 'sqlite/audit.sqlite' AS audit;
```

Doğrulama sorguları:

```sql
SELECT name
FROM raw.sqlite_master
WHERE type = 'table'
ORDER BY name;

SELECT 'subscribers' AS table_name, COUNT(*) AS row_count FROM raw.subscribers
UNION ALL SELECT 'cdr_events', COUNT(*) FROM raw.cdr_events
UNION ALL SELECT 'recharges', COUNT(*) FROM raw.recharges
UNION ALL SELECT 'plan_changes', COUNT(*) FROM raw.plan_changes;
```