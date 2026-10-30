-- Descriptive, not causal: lifetime cash by account attributes from current snapshot.
WITH paid AS (
  SELECT account_id, sum(try_cast(amount AS DOUBLE)) AS gross_successful_amount,
         count(DISTINCT payment_id) AS successful_events
  FROM read_csv_auto('output/preprocessed/golden/golden_payments.csv', header=true)
  WHERE payment_status='SUCCESS'
  GROUP BY account_id
)
SELECT a.risk_segment, count(DISTINCT a.account_id) AS file_accounts,
       count(DISTINCT p.account_id) AS accounts_with_success,
       sum(coalesce(p.gross_successful_amount,0)) AS gross_cash,
       count(DISTINCT p.account_id)::DOUBLE / nullif(count(DISTINCT a.account_id),0) AS payer_share
FROM read_csv_auto('output/preprocessed/golden/golden_accounts_current.csv', header=true) a
LEFT JOIN paid p USING(account_id)
GROUP BY a.risk_segment ORDER BY a.risk_segment;
-- Current DPD/status do not represent the historical value at payment time.
