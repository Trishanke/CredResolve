# Driver assessment: what can and cannot be explained

The assignment requests investigation across the dimensions below. This assessment separates data facts from causal evidence; the available extracts do not identify why cash moved month to month.

| Driver | Data available and observed result | Evidence class | Conclusion / limitation |
|---|---|---|---|
| Portfolio mix / borrower segment | Account loan type, risk segment, current status; all-window gross cash and payer share are in the segment CSVs. Risk-segment payer penetration spans about 43.7%–45.0%. | Fact + descriptive association | Current account attributes are not effective-dated and months are not mix-standardized. Not an explanation of the monthly trend. |
| DPD | Current account DPD spans 0–180; payer penetration by DPD bucket is about 43.4%–45.8%. | Fact + descriptive association | DPD is not observed at each payment date; do not interpret as DPD-specific recovery lift. |
| Client | No client identifier or client dimension is present. | Fact | Cannot analyze client mix. |
| Geography | Borrower city/state fields exist. Account-to-borrower join resolves for 27,087/30,000 accounts; 455 borrower IDs are null and 2,458 non-null IDs do not match the current borrower master. | Fact | State summaries are provided as descriptive only; missing identity links may bias geography comparisons. |
| Language | No language field in any supplied table. | Fact | Cannot analyze language effect. |
| Agent / tenure | Calls and sessions have agent IDs; agent file has 30,000 rows but only 1,000 agent IDs and multiple snapshots. Joined date exists, but historical effective-dated team/vendor/identity mapping and agent costs do not. | Fact; causal attribution unidentifiable | Current snapshot could support exploratory tenure cuts only; payment is not authoritatively attributable to an agent. No claim that tenure drove cash. |
| Campaign / targeting | 45,000 daily target rows; campaigns contain channel and strategy_version (legacy/v1/v2/v3). Exposure joins to lifetime cash are in `targeting_exposure_descriptive.csv`. | Association only | Accounts can be targeted repeatedly and cash may predate or follow exposure. No rollout date/holdout; do not infer uplift or counterfactual. |
| Channel | Call, SMS, WhatsApp, field, and campaign channels exist, but exposure and successful payments lack a validated attribution window. | Fact; causal attribution unidentifiable | Report touch volume separately; channel conversion/ROI cannot be trusted from a last-touch join. |
| Telephony vendor | Vendor IDs map to names/schema versions; call `ANSWERED` shares are approximately 19%–21% across vendors. | Descriptive association | `ANSWERED` is not RPC; no call cost/quality map, and vendor/campaign/agent mix confounds vendor comparisons. |
| Calling time | Event timestamps use mixed UTC/Kolkata/Dubai labels without reliable per-event offsets. | Fact | Local hour/day analysis is unsafe until timestamp timezone semantics are reconciled. |
| Attempt frequency | 120,000 attempts across 29,451 accounts; median 4 attempts/account in the observed window. Distribution is in `attempt_frequency_descriptive.csv`. | Fact; causal effect unknown | Attempt count is selected by collection difficulty and exposure; account cash by attempt band would not identify marginal attempt impact. |
| PTP | 4,489 KEPT and 4,553 BROKEN labels; KEPT share among closed labels is 49.65%. | Fact about labels | No independent payment-date matching; treat as source-coded proxy, not validated PTP kept performance. |

## What changed and why

The measured outcome is gross recorded successful payment amount. Complete-month movements alternate: Feb −9.1%, Mar +11.0%, Apr −7.3%, May +5.2%, Jun −4.7%, Jul +6.7%; August is incomplete. The dataset supports the **fact** that reported monthly cash is volatile and that one complete month is near +11%. It does not show a stable +11% month-over-month sequence.

The **hypothesis** that targeting, portfolio, channel, agent, or vendor changes caused the movements cannot be tested credibly from the supplied evidence. There is no explicit intervention date or random/credible control, and historical denominators, point-in-time attributes, costs, and payment attribution are incomplete. The recommended randomized targeting experiment is specified in `counterfactual_and_experiment.md`.
