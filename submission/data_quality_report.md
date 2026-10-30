# Data quality report

The source README says the dataset is synthetic and intentionally contains data defects. Raw inputs are preserved. Preprocessing rules and row-level counts are in [preprocessing report](../output/preprocessed/preprocessing_report.md).

## Key quantified findings

- 2,957 exact duplicate rows removed to quarantine across the event tables.
- Payments: 25,500 raw rows → 25,014 after exact dedupe → 25,000 canonical payment IDs.
- 14 repeated payment IDs differed only because one copy had a missing reference; the reference was safely coalesced within ID. No other payment-ID conflicts remained.
- 3,407 non-null references are reused across payment IDs; all 3,407 repeated references span multiple accounts and different amounts. Reference alone is not a dedupe key.
- 455 accounts have no borrower ID. The file has 30,000 account IDs; 13,284 distinct accounts have a recorded SUCCESS payment in the observed period.
- Observation window: 2026-01-01 00:14:40 to 2026-08-08 23:50:23; August is partial.

## Findings and treatment

| Issue | Evidence | Business impact | Treatment |
|---|---|---|---|
| Coverage | Payment and targeting tables span Jan 1-Aug 8, 2026 | Limits trend to 7 complete months; August partial | Keep Aug visibly partial; do not annualize |
| Missingness | 455 accounts lack borrower_id; 382 payments lack payment_reference; phones/emails and other fields missing | Can break borrower-level joins and payment deduplication | Preserve null; only coalesce a missing reference within same payment_id when all other facts agree |
| Exact duplicates | Borrowers, calls, payments and WhatsApp contain exact duplicate rows | Inflates event counts/amount if summed | Remove exact copies; retain quarantined raw copies |
| Payment ID conflicts | Repeated payment_id sometimes differs only by blank vs populated reference | Could double-count events | Coalesce only the non-null reference when all other payment facts agree; quarantine any other conflict |
| Payment reference reuse | Reference is reused across payment IDs/accounts/amounts | Reference alone is not a valid dedupe key | Do not deduplicate globally by reference |
| Agent identity | 30,000 agent rows map to 1,000 agent_ids | Agent snapshots/history, not one row per agent | Use latest updated_at only for current descriptive snapshot; avoid historical staffing attribution |
| Borrower identity | 30,600 rows map to repeated borrower_ids | Snapshot histories and inconsistent IDs complicate joins | Latest updated_at as current snapshot; retain unmatched IDs and flag |
| Timezone | UTC, Kolkata, Dubai, and timestamps without offsets coexist | Can shift day/hour attribution | No conversion in staging; retain source timezone and defer local-time analysis |
| Disposition codes | legacy/v1/v2 with codes including PTP and PROMISE_TO_PAY | No authoritative code map; RPC semantics unclear | Do not assert RPC/contact rate from disposition alone |
| Denominator | No historical eligible population/account status snapshot | Account recovery rate may have an unstable denominator | Report cash and file-account payer penetration as a proxy, not recovery rate |
| Causality/ROI | No intervention date, costs, channel price, agent wage, or holdout | Cannot estimate incremental ROI reliably | Run randomized targeting test and collect full cost data |

## Metric caveats

- SUCCESS status yields gross recorded cash, not independently reconciled net cash; reversed events cannot be linked with confidence.
- No currency column is supplied; ₹ interpretation follows the assignment context.
- Static account DPD/status are not aligned to each event date, so segment cuts are descriptive and can suffer temporal leakage.
- PTP kept share from labels is 4,489 / (4,489 + 4,553) = 49.65%; payment timing does not independently verify those labels.
- No single RPC mapping across legacy/v1/v2 disposition versions. No true contact rate is asserted.
- No client or language fields are available. Agent rows are snapshots; latest updated_at is current-only and not reliable for historical tenure.
- Costs, historical eligible population, targeting rollout assignment/date, and channel touch-to-payment links are absent; causal ROI and historical no-change counterfactual are not estimable.

## Conclusion

The observed data support a descriptive gross-cash trend after conservative payment normalization. They do not support a validated recovery rate, stable 11% monthly improvement, causal driver attribution, or ₹10 Cr ROI. The next step is a randomized, costed targeting pilot with a fixed denominator and reconciled outcomes.