#!/usr/bin/env python3
"""PostgreSQL raw yapısının DuckDB eşdeğerini oluşturur ve CSV'leri yükler."""

import argparse
import csv
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SCHEMA_PATH = ROOT / "sql" / "duckdb" / "00_schema.sql"
TABLES = {
    "subscribers": "raw_subscribers.csv",
    "cdr_events": "raw_cdr_events.csv",
    "recharges": "raw_recharges.csv",
    "campaigns": "raw_campaigns.csv",
    "campaign_responses": "raw_campaign_responses.csv",
    "plan_changes": "raw_plan_changes.csv",
    "plans": "raw_plans.csv",
    "corporate_accounts": "raw_corporate_accounts.csv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CSV verilerini DuckDB'ye yükler.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "duckdb" / "telco_dw.duckdb",
        help="DuckDB dosyası (varsayılan: duckdb/telco_dw.duckdb)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Mevcut DuckDB dosyasını silip yeniden oluşturur.",
    )
    return parser.parse_args()


def csv_columns(csv_path: Path) -> tuple[list[str], int]:
    with csv_path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.reader(source)
        columns = next(reader, None)
        if not columns:
            raise ValueError(f"{csv_path} CSV başlığı içermiyor.")
        return columns, sum(1 for _ in reader)


def load_table(connection: duckdb.DuckDBPyConnection, table_name: str, csv_name: str) -> int:
    csv_path = DATA_DIR / csv_name
    source_columns, source_count = csv_columns(csv_path)
    target_columns = [
        row[0]
        for row in connection.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'raw' AND table_name = ?
            ORDER BY ordinal_position
            """,
            [table_name],
        ).fetchall()
    ]
    if source_columns != target_columns:
        raise ValueError(
            f"{csv_path} başlıkları {table_name} şemasıyla eşleşmiyor: "
            f"beklenen {target_columns}, gelen {source_columns}"
        )

    escaped_path = str(csv_path.resolve()).replace("'", "''")
    connection.execute(
        f"COPY raw.{table_name} FROM '{escaped_path}' (HEADER, AUTO_DETECT FALSE)"
    )
    target_count = connection.execute(
        f"SELECT COUNT(*) FROM raw.{table_name}"
    ).fetchone()[0]
    if source_count != target_count:
        raise RuntimeError(
            f"raw.{table_name} satır sayısı uyuşmuyor: "
            f"kaynak={source_count}, hedef={target_count}"
        )
    return target_count


def main() -> None:
    args = parse_args()
    output_path = args.output.resolve()
    if output_path.exists():
        if not args.replace:
            raise FileExistsError(
                f"{output_path} zaten var. Yeniden oluşturmak için --replace kullanın."
            )
        output_path.unlink()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(output_path))
    try:
        connection.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
        for table_name, csv_name in TABLES.items():
            loaded_count = load_table(connection, table_name, csv_name)
            print(f"raw.{table_name}: {loaded_count} (doğrulandı)")
    finally:
        connection.close()


if __name__ == "__main__":
    main()