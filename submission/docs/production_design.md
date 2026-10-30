# Production analytics design

## Flow and responsibilities

The architecture diagram is in `architecture.mmd`. Implement each stage as idempotent, versioned transformations; retain raw inputs and source lineage.

### Raw → staging
- Land source extracts immutably with `source_system`, `extract_id`, `ingested_at`, checksum, schema version, and source file name.
- Validate file presence, encoding, header/schema, row counts, and parseability before loading.
- Store source fields as received plus normalized fields. Never overwrite raw data.
- Use separate event time, source-recorded time, and ingestion time.

### Clean → golden
- Clean tables retain source row ID, source system, extract ID, and transformation version.
- Declare primary keys and grains in a registry. Event IDs are idempotency keys; detect duplicate-key conflicts rather than choosing arbitrary last rows.
- Resolve borrower/agent IDs in effective-dated crosswalk tables with confidence and provenance; do not silently fuzzy-merge.
- Build payment facts only from successful, reconciled settlement events. Track reversals as linked negative events where processor IDs support it.
- Build account snapshots with `valid_from`, `valid_to`, `recorded_at`; never treat current status/DPD as historical state.
- Keep campaign exposure and recommendation distinct from actual delivery/touch and payment attribution.

### Feature → metric → dashboard
- Features are point-in-time correct: only attributes known before treatment/event can enter analysis.
- Maintain a versioned metric registry: name, owner, grain, numerator, denominator, inclusion/exclusion, currency, timezone, maturity window, and effective dates.
- Dashboard reads certified aggregate tables and shows freshness, partial periods, confidence intervals, definition version, and alerts.

## Keys and data contracts

- `account_id`, `borrower_id`, `agent_id`, `campaign_id`, `payment_id`, `call_id`, `attempt_id`, `disposition_id`, and provider message/visit/PTP IDs have explicit documented grains.
- Foreign-key validity is measured, not presumed. Null/unmatched key thresholds alert; rows are routed to a review queue without silently dropped joins.
- Status/event enums have versioned code maps and unknown values are quarantined for mapping review.
- Money has amount, ISO currency, event status, settlement reference, reversal reference, and source transaction ID; enforce nonnegative/allowed-sign rules by event type.
- Timestamps include UTC offset or IANA timezone on each event, plus source and ingestion timestamps.

## Incremental processing, late data, and backfills

- Partition immutable raw/clean event data by `event_date_utc` when available and source system.
- Upsert by stable event key plus source version; a replay of an extract must be idempotent.
- Maintain a rolling late-arrival window (initially 14 days, tune from observed lag distribution) and recompute affected partitions/account aggregates.
- Preserve corrected source versions. Backfills specify date range, source extract/version, transformation version, and reason; compare old/new aggregates before publish.
- Publish metrics only after the configured maturity window; mark recent dates provisional and restate with visible revision history.

## Data quality and monitoring

- Freshness: last extract by source, lag distribution, missing partitions.
- Volume: row count, distinct key count, expected ranges, abrupt changes.
- Integrity: exact duplicates, conflicting duplicate keys, null rates, foreign-key match rates, invalid amount/timestamp/enums.
- Financial reconciliation: source settlement totals versus golden net cash, payment status movement and reversal linkage, account balance constraints.
- Behavioral anomalies: recovery amount/rate, payer count, contact/answer rate, PTP kept rate, complaints, channel mix; compare with trailing baselines and same weekday/season when available.
- Alert on absolute and relative thresholds with severity, owner, affected metric, sample records, and runbook. Block publication for critical schema/key/financial failures; publish degraded with explicit warning for noncritical late feeds.
- Record every pipeline run, code commit, data versions, row counts, rejected rows, and metric revisions in lineage metadata.
