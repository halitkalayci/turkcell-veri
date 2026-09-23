#!/usr/bin/env python3
"""PostgreSQL raw yapısının SQLite eşdeğerini oluşturur ve CSV'leri yükler."""

import argparse
import csv
import shutil
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SCHEMA_PATH = ROOT / "sql" / "sqlite" / "00_schema.sql"
SCHEMAS = ("raw", "silver", "gold", "quarantine", "audit")
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
    parser = argparse.ArgumentParser(description="CSV verilerini SQLite'a yükler.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "sqlite",
        help="SQLite veritabanı dizini (varsayılan: sqlite)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Mevcut çıktı dizinini silip yeniden oluşturur.",
    )
    return parser.parse_args()


def boolean_value(value: str) -> int:
    normalized = value.strip().lower()
    if normalized in {"true", "t", "1"}:
        return 1
    if normalized in {"false", "f", "0"}:
        return 0
    raise ValueError(f"Geçersiz boolean değeri: {value!r}")


def prepare_output(output_dir: Path, replace: bool) -> None:
    if output_dir.exists():
        if not replace:
            raise FileExistsError(
                f"{output_dir} zaten var. Yeniden oluşturmak için --replace kullanın."
            )
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)


def attach_databases(connection: sqlite3.Connection, output_dir: Path) -> None:
    for schema_name in SCHEMAS:
        database_path = output_dir / f"{schema_name}.sqlite"
        connection.execute(f'ATTACH DATABASE ? AS "{schema_name}"', (str(database_path),))


def load_table(connection: sqlite3.Connection, table_name: str, csv_name: str) -> int:
    csv_path = DATA_DIR / csv_name
    with csv_path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames
        if not columns:
            raise ValueError(f"{csv_path} CSV başlığı içermiyor.")

        expected_columns = [column[1] for column in connection.execute(
            f'PRAGMA raw.table_info("{table_name}")'
        )]
        if columns != expected_columns:
            raise ValueError(
                f"{csv_path} başlıkları {table_name} şemasıyla eşleşmiyor: "
                f"beklenen {expected_columns}, gelen {columns}"
            )

        placeholders = ", ".join("?" for _ in columns)
        quoted_columns = ", ".join(f'"{column}"' for column in columns)
        insert_sql = f'INSERT INTO raw."{table_name}" ({quoted_columns}) VALUES ({placeholders})'
        rows = []
        source_count = 0
        for row in reader:
            values = [row[column] for column in columns]
            if table_name == "campaign_responses":
                values[columns.index("accepted")] = boolean_value(row["accepted"])
            rows.append(values)
            source_count += 1
            if len(rows) == 10_000:
                connection.executemany(insert_sql, rows)
                rows.clear()
        if rows:
            connection.executemany(insert_sql, rows)
    target_count = connection.execute(
        f'SELECT COUNT(*) FROM raw."{table_name}"'
    ).fetchone()[0]
    if source_count != target_count:
        raise RuntimeError(
            f"raw.{table_name} satır sayısı uyuşmuyor: "
            f"kaynak={source_count}, hedef={target_count}"
        )
    return target_count


def main() -> None:
    args = parse_args()
    output_dir = args.output.resolve()
    prepare_output(output_dir, args.replace)

    connection = sqlite3.connect(output_dir / "telco_dw.sqlite")
    try:
        attach_databases(connection, output_dir)
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        for table_name, csv_name in TABLES.items():
            loaded_count = load_table(connection, table_name, csv_name)
            print(f"raw.{table_name}: {loaded_count} (doğrulandı)")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()