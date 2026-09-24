---
applyTo: "airflow/**"
---
# Airflow kuralları (2.x, TaskFlow)
- Her DAG'da zorunlu: sabit start_date (datetime(...)), catchup=False, max_active_runs=1, default_args'ta retries>=3 + retry_exponential_backoff, tags, doc_md.
- Sensor'ler mode='reschedule' ve timeout ile; poke_interval >= 60.
- Tarih her zaman {{ ds }} / data_interval_start'tan; date.today() / datetime.now() task içinde KULLANILMAZ.
- Bağlantı ve şifre koda gömülmez: env var ya da conn_id.
- Yükleme task'ları idempotent: aynı ds için önce DELETE sonra INSERT (ya da ON CONFLICT).
- dbt adımları BashOperator ile: dbt run/test/snapshot --project-dir ... --profiles-dir ...; staging → test → snapshot → marts → test sırası.
- @task.branch kullanılıyorsa birleşme task'ında trigger_rule='none_failed_min_one_success'.
- Dynamic task mapping'de max_active_tis_per_dag ile paralellik sınırlanır.