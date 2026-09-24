---
description: "Airflow DAG üret — airflow.instructions.md kurallarıyla"
---

dag_id \${input:dag_id} için airflow/dags/\${input:dag_id}.py yaz. Amaç: \${input:goal}.
Zorunlu: TaskFlow API; sabit start_date; catchup=False; max_active_runs=1; default_args retries>=3 + retry_exponential_backoff; sensor'ler mode='reschedule' + timeout; tarih {{ ds }}; şifre/bağlantı env veya conn_id; yükleme idempotent (DELETE+INSERT); dbt adımları BashOperator ile --project-dir/--profiles-dir; her task'a doc_md; DAG'a doc_md ve tags.
Bitince: airflow dags test \${input:dag_id} 2026-09-01 komutunu ver; hangi varsayımları yaptığını ve instructions'a eklenecek yeni kural varsa öner.