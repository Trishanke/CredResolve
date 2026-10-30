# Executive memo — Collections recovery review

**Decision:** The supplied data do not substantiate a sustained 11% month-on-month recovery improvement. The defensible observation is gross successful payment amount; the data do not support a stable historical recovery-rate denominator, causal channel lift, or reliable ₹10 Cr ROI.

## What happened?

The files contain payment events from 1 Jan through 8 Aug 2026, with seven complete months (Jan–Jul) and a partial August. After removing exact duplicates and resolving same-payment-ID rows that differ only by a missing reference, recorded SUCCESS payments total **₹131.56 Cr** for the observed window, assuming amounts are INR. Monthly gross cash is volatile: February changed **−9.1%** month-on-month, March **+11.0%**, April **−7.3%**, May **+5.2%**, June **−4.7%**, and July **+6.7%**. March is near +11%, but it is one month; August is partial and must not be compared as a full month. This is gross recorded cash, not a validated recovery rate.

## Why / confidence

**Facts:** raw records include exact duplicates, repeated IDs, null identifiers, mixed timezone labels, several disposition-code versions, and reused payment references. Canonical payment references repeat across different payment IDs, accounts, and amounts, so a reference alone cannot deduplicate. The account file contains 30,000 accounts, but 455 lack borrower IDs; account status is not historically effective-dated.

**Strong evidence:** after conservative event cleaning, monthly recorded payment totals do not show a consistent +11% path. **Unknown:** whether composition, targeting, operations, or attribution caused those movements. DPD/status are not time-aligned to each payment, there is no explicit targeting intervention date or credible control group, and the data contain no costs. Channel last-touch associations would be selected and attribution-window dependent. Confidence is high for the listed data defects and recorded cash totals; low for business-level recovery rates and causes.

## Recommendation and financial impact

Recommend **better borrower targeting as a controlled pilot**, not a proven ₹10 Cr scale decision. The pilot tests a measurable policy and can establish whether scaling is justified.

| Item | Assessment |
|---|---|
| Expected incremental recovery | Not estimable from supplied history. Measure treatment-control difference in 30-day net settled cash per eligible assigned account; scale by verified eligible volume only after the test. |
| Estimated cost | A ₹10 Cr cap is specified by the assignment, but no vendor, technology, or operating cost schedule is supplied. Pilot and full-scale cost cannot be estimated from these files. |
| Expected ROI | Not estimable without incremental cash and fully loaded costs. Do not report a fabricated point estimate or confidence range. |
| Break-even | Over the chosen horizon, incremental net settled cash must exceed ₹10 Cr plus recurring incremental operating cost. |
| Key assumptions | Random assignment is preserved; a fixed eligibility denominator is used; outcomes mature for 30 days; settlements/reversals and costs are complete; spillover is controlled. |
| Downside | Zero or negative net lift after cost, operational capacity constraints, or higher complaint/opt-out rates. Monitor complaints and contact frequency as guardrails. |
| Confidence | High that current files are insufficient for ROI; low on the direction and size of targeting lift until randomized evidence exists. |

Use a stratified randomized holdout: current policy as control versus proposed targeting as treatment, stratified by client, DPD, risk, geography, and month. Keep 10% control, enroll for at least eight weeks, then allow 30 days for outcome maturity. Set the final duration and sample size from baseline variance and a pre-registered minimum detectable effect. Before scaling, add transaction settlement/reversal linkage, historical eligible-account snapshots, explicit targeting rollout/exposure timestamps, canonical local time, and channel/agent/vendor costs.
