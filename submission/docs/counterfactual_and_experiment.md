# Counterfactual and experiment plan

## Why the historical counterfactual is not identified

The supplied files do not specify the date on which targeting changed, a consistent treatment assignment, or an untreated comparison population. Campaign strategy versions overlap, and daily_targeting records exposure/queue status rather than randomized assignment. Targeted accounts differ by selection and can have multiple touches. A before/after comparison would mix seasonality, portfolio composition, and selection effects; matching/regression cannot repair missing assignment or unobserved confounders. No reliable causal estimate is produced from the historical data.

## Prospective randomized test of better borrower targeting

- **Population:** eligible account-days before any strategy assignment; establish one canonical eligibility rule, suppress legally/operationally ineligible accounts, and freeze it before randomization.
- **Treatment:** proposed targeting policy ranks/selects accounts and assigns recommended action.
- **Control:** current targeting policy, with business-as-usual contact rules.
- **Randomization:** assign accounts within client, DPD, risk, geography, and month strata. If agents/capacity create spillover across accounts, randomize at team/region cluster and use cluster-robust inference.
- **Primary outcome:** intention-to-treat net settled cash within 30 days per eligible assigned account, with account exposure denominator fixed at assignment. Reconcile reversals before outcome lock.
- **Guardrails:** complaint rate/severity, opt-outs, contact frequency, promise broken rate, and treatment cost.
- **Duration:** at least 8 weeks of enrollment plus 30 days for outcomes to mature; choose final duration and sample size from baseline variance and minimum detectable effect before launch.
- **Identification assumptions:** random assignment is preserved; outcome collection is complete and equally mature; no differential exclusions; spillover is controlled by cluster design; consistent treatment and outcome definitions.
- **Analysis:** ITT difference in mean net cash per assigned account with confidence interval; stratification covariates improve precision. Report per-protocol only as secondary.
- **Limitations:** one portfolio/season may not generalize; operational capacity and customer behavior may change; estimate applies to tested targeting policy and cost level.

## Scale decision

Compute incremental net benefit = (treatment-control net cash per eligible account × scale eligible account count) − incremental operating and technology cost. ROI = incremental net benefit / invested amount. Break-even requires incremental net cash to cover the ₹10 Cr investment plus recurring incremental cost over the chosen horizon. The current data cannot populate these terms; do not fabricate a point estimate or range.
