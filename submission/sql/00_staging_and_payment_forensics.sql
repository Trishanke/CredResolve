-- DuckDB SQL examples. Run from repository root; raw files stay immutable.
CREATE OR REPLACE VIEW raw_payments AS
SELECT * FROM read_csv_auto('collections_30k_dataset (1)/payments.csv', header=true, all_varchar=true);
CREATE OR REPLACE VIEW raw_accounts AS
SELECT * FROM read_csv_auto('collections_30k_dataset (1)/accounts.csv', header=true, all_varchar=true);
CREATE OR REPLACE VIEW raw_calls AS
SELECT * FROM read_csv_auto('collections_30k_dataset (1)/calls.csv', header=true, all_varchar=true);

-- Whitespace normalization and blank-to-null. Typed parsing is performed in Python
-- staging script so malformed values can be written to quarantine with source row.
CREATE OR REPLACE VIEW payments_normalized AS
SELECT NULLIF(trim(payment_id), '') AS payment_id,
       NULLIF(trim(account_id), '') AS account_id,
       NULLIF(trim(borrower_id), '') AS borrower_id,
       NULLIF(trim(event_at), '') AS event_at,
       NULLIF(trim(payment_reference), '') AS payment_reference,
       try_cast(NULLIF(trim(amount), '') AS DOUBLE) AS amount,
       upper(NULLIF(trim(payment_status), '')) AS payment_status,
       upper(NULLIF(trim(payment_method), '')) AS payment_method,
       NULLIF(trim(provider_id), '') AS provider_id
FROM raw_payments;

-- Exact normalized duplicate diagnostic. Do not globally dedupe on reference.
SELECT payment_id, count(*) AS rows_per_id,
       count(DISTINCT account_id) AS accounts,
       count(DISTINCT amount) AS amounts,
       count(DISTINCT payment_status) AS statuses,
       count(DISTINCT payment_reference) AS references
FROM payments_normalized
GROUP BY payment_id HAVING count(*) > 1
ORDER BY rows_per_id DESC;

-- Reused transaction reference diagnostic. Same reference appears on distinct
-- accounts/amounts in this dataset; it is not a global transaction key.
SELECT payment_reference, count(*) AS rows,
       count(DISTINCT payment_id) AS payment_ids,
       count(DISTINCT account_id) AS accounts,
       count(DISTINCT amount) AS amounts
FROM payments_normalized
WHERE payment_reference IS NOT NULL
GROUP BY payment_reference HAVING count(*) > 1
ORDER BY rows DESC;
