# Data quality and metric contract

## Entity and event grain

| Table | Intended key / grain | Handling |
|---|---|---|
| accounts | account_id; current supplied row | Keep one record per source row; borrower_id may be null/unmatched |
| borrowers | borrower_id snapshots | Current master selects latest updated_at; retain lineage |
| agents | agent_id snapshots | Current master selects latest updated_at; never use as historical staffing truth |
| payments | payment_id transaction event | Exact duplicates removed; missing reference coalesced only within same ID when all facts agree; conflicting groups quarantined |
| calls | call_id call event | Exact duplicate rows removed; conflicting IDs flagged, no latest-wins assumption |
| call_attempts / dispositions | attempt_id / disposition_id event | Exact duplicate removal only; disposition mapping version-aware |
| daily_targeting | target_id target exposure | Preserve repeat account targets; exposure is not treatment assignment |
| PTP | ptp_id promise event | Preserve source outcome; KEPT/BROKEN proxy only |
| account_status_history | history_id status event | Preserve event_at and recorded_at separately; no overwrite collapse |

## Metric definitions

- **Gross successful recorded cash:** sum amount for canonical payment IDs where payment_status = SUCCESS. Not net settled cash: reversal linkage and currency are not supplied.
- **Monthly cash:** group gross successful cash by event_at month. Source event times have mixed timezone semantics; keep original local clock for now. August ends Aug 8 and is partial.
- **Payer count:** distinct accounts with a successful payment in that month.
- **Payer penetration proxy:** monthly payer count / 30,000 account IDs in the supplied account file. It is not a recovery rate because historical eligible/active denominator is missing.
- **Cash per file account:** monthly gross cash / 30,000 supplied account IDs, descriptive only.
- **PTP kept proxy:** KEPT / (KEPT + BROKEN) according to supplied PTP labels. Excludes open/cancelled; not verified against dated payments.
- **Contact / RPC:** not reported. ANSWERED is not proof of right-party contact; legacy/v1/v2 code mapping is absent.
- **Channel conversion / attribution:** not reported as causal. A target or touch is not linked to a payment by an authoritative window.
- **Cost per rupee recovered / ROI:** not computable; no channel costs, agent costs, or currency field.

## Missingness and exclusions

Null remains null. Do not impute borrower IDs, transaction references, timestamps, phone/email, or balances. Rows with exact duplicate normalized content are removed from clean staging and preserved under quarantine. Payment IDs with the same amount/account/time/status/method/provider but one missing reference are coalesced to one event using the available reference. Other conflicts go to quarantine. Payment references are not globally unique. No outlier clipping or business-row filtering is applied.

## Timestamp policy

Preserve event wall-clock values and source timezone labels. Do not convert to UTC unless the event's own timezone is authoritative. For operational hour/day metrics, require one canonical event timezone and daylight/offset metadata. Keep event_at (business time), recorded_at (system ingestion/recording time), and ingestion time separately in production.

## Known input limits

- Observed event period: 2026-01-01 through 2026-08-08, not 12 months.
- No effective-dated historical active-account denominator or balance history.
- No authoritative payment settlement/reversal link; success values are gross.
- No client or language fields in the supplied tables.
- Campaign strategy versions exist, but there is no explicit intervention/rollout date or assignment mechanism.
- No channel/agent/vendor cost tables; ROI is not estimable.
