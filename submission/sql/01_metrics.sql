-- Golden payment aggregation. The Python build step creates golden_payments.csv
-- by exact-row dedupe and coalescing a missing payment_reference only within the
-- same payment_id when all other facts agree. Conflicts go to quarantine.
CREATE OR REPLACE VIEW payments_golden AS
SELECT * FROM read_csv_auto('output/preprocessed/golden/golden_payments.csv', header=true);

CREATE OR REPLACE VIEW monthly_gross_success AS
SELECT strftime(try_cast(event_at AS TIMESTAMP), '%Y-%m') AS month,
       count(DISTINCT payment_id) AS successful_payment_events,
       sum(try_cast(amount AS DOUBLE)) AS gross_successful_amount,
       count(DISTINCT account_id) AS distinct_paying_accounts
FROM payments_golden
WHERE payment_status='SUCCESS'
  AND try_cast(event_at AS TIMESTAMP) IS NOT NULL
GROUP BY 1;

WITH metrics AS (
  SELECT *, lag(gross_successful_amount) OVER (ORDER BY month) AS prior_amount
  FROM monthly_gross_success
)
SELECT month, successful_payment_events, gross_successful_amount,
       distinct_paying_accounts,
       100.0 * (gross_successful_amount / nullif(prior_amount,0) - 1) AS mom_change_pct,
       month <> '2026-08' AS month_complete
FROM metrics ORDER BY month;

-- PTP label proxy only. Not independently checked against a dated payment event.
SELECT count(*) FILTER (WHERE status='KEPT') AS kept,
       count(*) FILTER (WHERE status='BROKEN') AS broken,
       count(*) FILTER (WHERE status='KEPT')::DOUBLE /
         nullif(count(*) FILTER (WHERE status IN ('KEPT','BROKEN')),0) AS kept_share
FROM read_csv_auto('output/preprocessed/promises_to_pay.csv', header=true);
