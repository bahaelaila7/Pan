#!/usr/bin/env sh
OUTPUT_DIR=./outputs
PARQUET_DIR="${OUTPUT_DIR}"
TABLE_NAME="output_communities"
rm "${PARQUET_DIR}"/*.*db

duckdb "${OUTPUT_DIR}/outputs.duckdb" -c "
CREATE TABLE ${TABLE_NAME} AS 
SELECT * FROM read_parquet('${PARQUET_DIR}/**/*.parquet');
"

duckdb -c "install sqlite; load sqlite;"
duckdb -c "ATTACH '${OUTPUT_DIR}/outputs.db' AS sqlite_db (TYPE SQLITE);
CREATE TABLE sqlite_db.${TABLE_NAME} AS
SELECT * FROM read_parquet('${PARQUET_DIR}/**/*.parquet');"
