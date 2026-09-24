"""Her gece raw.cdr_events'e günlük CDR dosyasını yükleyip dbt pipeline'ını çalıştırır."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import duckdb
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor

# Bağlantı/yol bilgileri env var'dan okunur; koda gömülmez.
DATA_DIR = os.environ.get("DATA_DIR", "/opt/airflow/data")
DUCKDB_PATH = os.environ.get("DUCKDB_PATH", "/opt/airflow/duckdb/telco_dw.duckdb")
DBT_PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/opt/airflow/dbt")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", "/opt/airflow/dbt")
# dbt proje klasörü read-only mount edildiği için target/log çıktıları /tmp'ye yazılır.
DBT_ARTIFACT_DIR = os.environ.get("DBT_ARTIFACT_DIR", "/tmp/dbt_artifacts")

DBT_COMMON_FLAGS = (
    f"--project-dir {DBT_PROJECT_DIR} "
    f"--profiles-dir {DBT_PROFILES_DIR} "
    f"--target-path {DBT_ARTIFACT_DIR}/target "
    f"--log-path {DBT_ARTIFACT_DIR}/logs"
)

# Kaynak dosyada beklenen ~%2 duplicate oranının çok üzerini anomali sayıyoruz.
MAX_EXPECTED_DUPLICATE_RATIO = 0.10

default_args = {
    "owner": "data-eng",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}


@dag(
    dag_id="cdr_daily_pipeline",
    description="Günlük CDR dosyasını raw'a yükler, doğrular ve dbt staging->snapshot->marts pipeline'ını çalıştırır.",
    schedule="0 3 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["cdr", "raw", "dbt", "gold", "daily"],
    doc_md="""
    ### CDR Günlük Yükleme + dbt Pipeline

    Her gece 03:00'te çalışır:
    1. `data/incoming/cdr_{{ ds }}.csv` dosyasını bekler (mode=reschedule).
    2. `raw.cdr_events`'e ilgili gün için idempotent yükler (DELETE + INSERT).
    3. Satır sayısı ve duplicate oranını doğrular.
    4. dbt staging -> test -> snapshot -> marts -> test sırasını çalıştırır.

    **Varsayımlar:**
    - `cdr_{{ ds }}.csv` dosyasındaki olayların `event_ts` tarihi `ds` gününe aittir;
      idempotent DELETE bu varsayıma göre `event_ts::DATE = ds` filtresiyle yapılır.
    - DuckDB dosyasına tek seferde bir process erişir (Airflow worker ile dbt subprocess'i
      sıralı çalışır, aynı anda açık bağlantı olmaz).
    - `dbt_packages/` repo içinde vendored olduğu için `dbt deps` adımına gerek yok.
    """,
)
def cdr_daily_pipeline():
    wait_for_cdr_file = FileSensor(
        task_id="wait_for_cdr_file",
        fs_conn_id="fs_default",
        filepath=f"{DATA_DIR}/incoming/cdr_{{{{ ds }}}}.csv",
        mode="reschedule",
        poke_interval=60,
        timeout=60 * 60 * 6,
        doc_md="`data/incoming/cdr_{{ ds }}.csv` dosyası oluşana kadar reschedule modunda bekler (timeout 6 saat).",
    )

    @task(doc_md="CSV'yi okuyup `raw.cdr_events`'e ilgili `ds` günü için DELETE+INSERT ile idempotent yükler.")
    def load_cdr_to_raw(ds: str | None = None) -> dict:
        csv_path = f"{DATA_DIR}/incoming/cdr_{ds}.csv"
        con = duckdb.connect(DUCKDB_PATH)
        try:
            con.execute("BEGIN TRANSACTION")
            con.execute(
                "DELETE FROM raw.cdr_events WHERE CAST(event_ts AS DATE) = CAST(? AS DATE)",
                [ds],
            )
            con.execute(
                """
                INSERT INTO raw.cdr_events
                SELECT
                    event_id, msisdn, event_type, event_ts,
                    duration_sec, bytes, cell_id, country_code, ingested_at
                FROM read_csv_auto(?, header=True)
                """,
                [csv_path],
            )
            con.execute("COMMIT")
            inserted_rows = con.execute(
                "SELECT count(*) FROM raw.cdr_events WHERE CAST(event_ts AS DATE) = CAST(? AS DATE)",
                [ds],
            ).fetchone()[0]
        except Exception:
            con.execute("ROLLBACK")
            raise
        finally:
            con.close()
        return {"ds": ds, "inserted_rows": inserted_rows}

    @task(doc_md="Yüklenen gün için satır sayısı sıfır olamaz; duplicate oranı beklenen ~%2 aralığının çok üzerindeyse (>%10) task fail olur.")
    def validate_cdr_load(load_result: dict) -> None:
        ds = load_result["ds"]
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        try:
            total_rows, distinct_event_ids = con.execute(
                """
                SELECT count(*), count(DISTINCT event_id)
                FROM raw.cdr_events
                WHERE CAST(event_ts AS DATE) = CAST(? AS DATE)
                """,
                [ds],
            ).fetchone()
        finally:
            con.close()

        if total_rows == 0:
            raise ValueError(f"{ds} için raw.cdr_events içinde hiç satır bulunamadı.")

        duplicate_ratio = 1 - (distinct_event_ids / total_rows)
        print(
            f"[{ds}] total_rows={total_rows} distinct_event_id={distinct_event_ids} "
            f"duplicate_ratio={duplicate_ratio:.4f}"
        )
        if duplicate_ratio > MAX_EXPECTED_DUPLICATE_RATIO:
            raise ValueError(
                f"{ds} için duplicate oranı beklenenin çok üzerinde: {duplicate_ratio:.2%} "
                f"(eşik: {MAX_EXPECTED_DUPLICATE_RATIO:.0%})"
            )

    dbt_run_staging = BashOperator(
        task_id="dbt_run_staging",
        bash_command=f"dbt run --select staging {DBT_COMMON_FLAGS}",
        doc_md="`dbt run --select staging`: silver katmanı staging modellerini çalıştırır.",
    )

    dbt_test_staging = BashOperator(
        task_id="dbt_test_staging",
        bash_command=f"dbt test --select staging {DBT_COMMON_FLAGS}",
        doc_md="`dbt test --select staging`: staging modelleri için schema/data testlerini çalıştırır.",
    )

    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command=f"dbt snapshot {DBT_COMMON_FLAGS}",
        doc_md="`dbt snapshot`: `snap_subscriber_plan` snapshot'ını günceller.",
    )

    dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command=f"dbt run --select marts {DBT_COMMON_FLAGS}",
        doc_md="`dbt run --select marts`: gold katmanı mart modellerini (ör. `dim_subscriber`) çalıştırır.",
    )

    dbt_test_marts = BashOperator(
        task_id="dbt_test_marts",
        bash_command=f"dbt test --select marts {DBT_COMMON_FLAGS}",
        doc_md="`dbt test --select marts`: gold katmanı mart modelleri için testleri çalıştırır.",
    )

    load_result = load_cdr_to_raw()
    validate_result = validate_cdr_load(load_result)

    (
        wait_for_cdr_file
        >> load_result
        >> validate_result
        >> dbt_run_staging
        >> dbt_test_staging
        >> dbt_snapshot
        >> dbt_run_marts
        >> dbt_test_marts
    )


cdr_daily_pipeline()
