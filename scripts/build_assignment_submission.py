#!/usr/bin/env python3
"""Build conservative golden facts and assignment deliverables from cleaned tables."""
from pathlib import Path
import json, math
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
CLEAN=ROOT/'output'/'preprocessed'
GOLD=CLEAN/'golden'; QUAR=CLEAN/'quarantine'
SUB=ROOT/'submission'
GOLD.mkdir(parents=True,exist_ok=True); QUAR.mkdir(parents=True,exist_ok=True)

def load(name, **kwargs): return pd.read_csv(CLEAN/f'{name}.csv', **kwargs)
def write(df,path): df.to_csv(path,index=False)

# Canonicalize payments by stable payment_id. Exact duplicates were already removed.
p=load('payments',dtype={'payment_id':'string','account_id':'string','payment_reference':'string'})
p['payment_reference']=p.payment_reference.fillna('').astype(str).str.strip()
canonical=[]; unresolved=[]; decisions=[]
for pid,g in p.groupby('payment_id',dropna=False,sort=False):
    if len(g)==1:
        canonical.append(g.iloc[0].to_dict()); continue
    compare=[c for c in g.columns if c not in ('payment_reference','source_file','source_row_number')]
    # Treat reference missingness as a correctable field only if all payment facts agree.
    if all(g[c].nunique(dropna=False)<=1 for c in compare):
        row=g.sort_values('payment_reference',key=lambda s:s.str.len(),ascending=False).iloc[0].to_dict()
        refs=sorted(set(x for x in g.payment_reference if x))
        if len(refs)<=1:
            row['payment_reference']=refs[0] if refs else ''
            canonical.append(row)
            decisions.append({'payment_id':pid,'rows_collapsed':len(g),'rule':'same payment facts; coalesced non-null reference','reference':row['payment_reference']})
        else:
            for _,r in g.iterrows(): unresolved.append({**r.to_dict(),'quarantine_reason':'same payment_id has multiple distinct references'})
    else:
        for _,r in g.iterrows(): unresolved.append({**r.to_dict(),'quarantine_reason':'conflicting facts for repeated payment_id'})

pay=pd.DataFrame(canonical)
if unresolved:
    pd.DataFrame(unresolved).to_csv(QUAR/'payments_unresolved_id_conflicts.csv',index=False)
if decisions: pd.DataFrame(decisions).to_csv(GOLD/'payment_id_coalescing_log.csv',index=False)
write(pay,GOLD/'golden_payments.csv')

# Explicit current master snapshots: latest updated_at is only suitable for current descriptive joins.
for table,key in [('borrowers','borrower_id'),('agents','agent_id')]:
    d=load(table,dtype={key:'string'})
    d['updated_at_parsed']=pd.to_datetime(d.updated_at,errors='coerce')
    d=d.sort_values(['updated_at_parsed','source_row_number'],kind='stable')
    current=d.groupby(key,dropna=False,as_index=False).tail(1).drop(columns=['updated_at_parsed'])
    write(current,GOLD/f'golden_{table}_current.csv')

accounts=load('accounts',dtype={'account_id':'string','borrower_id':'string'})
write(accounts,GOLD/'golden_accounts_current.csv')

# Account x month panel. This is a recorded-account-set panel, not historical active exposure.
pay['event_dt']=pd.to_datetime(pay.event_at,errors='coerce')
pay['month']=pay.event_dt.dt.to_period('M').astype('string')
success=pay[pay.payment_status.eq('SUCCESS') & pay.event_dt.notna()].copy()
monthly=success.groupby('month',dropna=True).agg(
    successful_payment_events=('payment_id','nunique'),
    gross_successful_amount=('amount','sum'),
    distinct_paying_accounts=('account_id','nunique')
).reset_index()
months=pd.period_range('2026-01','2026-08',freq='M').astype(str)
monthly=monthly.set_index('month').reindex(months,fill_value=0).rename_axis('month').reset_index()
monthly['dataset_accounts']=accounts.account_id.nunique()
monthly['payer_penetration_of_file_accounts']=monthly.distinct_paying_accounts/monthly.dataset_accounts
monthly['gross_successful_amount_per_file_account']=monthly.gross_successful_amount/monthly.dataset_accounts
monthly['month_complete']=monthly.month.ne('2026-08')
monthly['mom_change_pct']=monthly.gross_successful_amount.pct_change()*100
write(monthly,GOLD/'golden_monthly_recovery.csv')

# Golden account-month fact; rows with no qualifying payment are explicit zeroes.
base=pd.MultiIndex.from_product([accounts.account_id.dropna().unique(),months],names=['account_id','month']).to_frame(index=False)
acct_success=success.groupby(['account_id','month'],dropna=False).agg(
    successful_payment_events=('payment_id','nunique'),gross_successful_amount=('amount','sum')
).reset_index()
panel=base.merge(acct_success,on=['account_id','month'],how='left')
panel[['successful_payment_events','gross_successful_amount']]=panel[['successful_payment_events','gross_successful_amount']].fillna(0)
panel['successful_payment_events']=panel.successful_payment_events.astype(int)
panel['has_successful_payment']=(panel.successful_payment_events>0).astype(int)
write(panel,GOLD/'golden_account_month_recovery.csv')

# Explicit observed definitions and descriptive side metrics.
ptp=load('promises_to_pay')
ptp_closed=ptp[ptp.status.isin(['KEPT','BROKEN'])]
ptp_rate=float((ptp.status=='KEPT').sum()/len(ptp_closed)) if len(ptp_closed) else None
calls=load('calls')
call_month=pd.DataFrame()
calls['event_dt']=pd.to_datetime(calls.event_at,errors='coerce')
calls['month']=calls.event_dt.dt.to_period('M').astype('string')
call_month=calls.assign(month=calls.event_dt.dt.to_period('M').astype('string')).groupby('month').agg(call_rows=('call_id','size'),distinct_calls=('call_id','nunique'),answered_status_rows=('call_status',lambda s:(s=='ANSWERED').sum())).reset_index()
call_month['answer_status_share']=call_month.answered_status_rows/call_month.call_rows
write(call_month,SUB/'call_volume_by_month.csv')

# High-level quality reconciliations
raw_pay=pd.read_csv(ROOT/'collections_30k_dataset (1)'/'payments.csv')
repay=pay.groupby('payment_id').size()
refgroups=pay[pay.payment_reference.fillna('').ne('')].groupby('payment_reference').agg(rows=('payment_id','size'),accounts=('account_id','nunique'),amounts=('amount','nunique'))
ref_repeats=refgroups[refgroups.rows>1]
months_range=(pd.to_datetime(pay.event_at,errors='coerce').min(),pd.to_datetime(pay.event_at,errors='coerce').max())
report={
 'payment_rows_raw':len(raw_pay),'payment_rows_after_exact_dedupe':len(load('payments')),'payment_id_canonical_rows':len(pay),
 'payment_id_duplicate_groups_pre_canonical':int(load('payments').payment_id.duplicated(keep=False).groupby(load('payments').payment_id).any().sum()),
 'payment_id_rows_coalesced':int(sum(x['rows_collapsed']-1 for x in decisions)), 'payment_unresolved_rows':len(unresolved),
 'distinct_payment_references_reused':int(len(ref_repeats)),
 'reused_references_with_multiple_accounts':int((ref_repeats.accounts>1).sum()),
 'reused_references_with_multiple_amounts':int((ref_repeats.amounts>1).sum()),
 'successful_amount_total':float(success.amount.sum()),'successful_event_count':int(success.payment_id.nunique()),
 'successful_paying_accounts_total':int(success.account_id.nunique()),
 'ptp_kept_rate_among_kept_or_broken':ptp_rate,'ptp_kept_count':int((ptp.status=='KEPT').sum()),'ptp_broken_count':int((ptp.status=='BROKEN').sum()),
 'account_count':int(accounts.account_id.nunique()),'borrower_id_missing_in_accounts':int(accounts.borrower_id.isna().sum()),
 'observation_start':str(months_range[0]),'observation_end':str(months_range[1]),
 'assumption_amount_currency':'INR inferred from assignment context; no currency column is provided',
 'limitations':['August 2026 is partial (events observed only through Aug 8).','No historical eligible-account denominator or as-of account status is available; payer penetration is only against the file account set.','No payment reversal linkage is supplied; SUCCESS is gross booked amount, not independently reconciled net cash.','No currency or cost data exists.','No authoritative timezone per event, RPC disposition map, targeting intervention timestamp, or stable treatment/control design exists.']
}
(SUB/'analysis_summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

# Monthly table with presentation-friendly rounded figures and evidence labels.
monthly_out=monthly.copy(); monthly_out['gross_successful_amount']=monthly_out.gross_successful_amount.round(2);monthly_out['mom_change_pct']=monthly_out.mom_change_pct.round(2);monthly_out['gross_successful_amount_per_file_account']=monthly_out.gross_successful_amount_per_file_account.round(2);monthly_out['payer_penetration_of_file_accounts']=(monthly_out.payer_penetration_of_file_accounts*100).round(2)
write(monthly_out,SUB/'monthly_recovery_metrics.csv')

# Machine-readable quality issues / disposition.
issues=[
('Coverage','Payment and targeting tables span Jan 1-Aug 8, 2026','Limits trend to 7 complete months; August partial','Keep Aug visibly partial; do not annualize'),
('Missingness','455 accounts lack borrower_id; 382 payments lack payment_reference; phones/emails and other fields missing','Can break borrower-level joins and payment deduplication','Preserve null; only coalesce a missing reference within same payment_id when all other facts agree'),
('Exact duplicates','Borrowers, calls, payments and WhatsApp contain exact duplicate rows','Inflates event counts/amount if summed','Remove exact copies; retain quarantined raw copies'),
('Payment ID conflicts','Repeated payment_id sometimes differs only by blank vs populated reference','Could double-count events','Coalesce only the non-null reference when all other payment facts agree; quarantine any other conflict'),
('Payment reference reuse','Reference is reused across payment IDs/accounts/amounts','Reference alone is not a valid dedupe key','Do not deduplicate globally by reference'),
('Agent identity','30,000 agent rows map to 1,000 agent_ids','Agent snapshots/history, not one row per agent','Use latest updated_at only for current descriptive snapshot; avoid historical staffing attribution'),
('Borrower identity','30,600 rows map to repeated borrower_ids','Snapshot histories and inconsistent IDs complicate joins','Latest updated_at as current snapshot; retain unmatched IDs and flag'),
('Timezone','UTC, Kolkata, Dubai, and timestamps without offsets coexist','Can shift day/hour attribution','No conversion in staging; retain source timezone and defer local-time analysis'),
('Disposition codes','legacy/v1/v2 with codes including PTP and PROMISE_TO_PAY','No authoritative code map; RPC semantics unclear','Do not assert RPC/contact rate from disposition alone'),
('Denominator','No historical eligible population/account status snapshot','Account recovery rate may have an unstable denominator','Report cash and file-account payer penetration as a proxy, not recovery rate'),
('Causality/ROI','No intervention date, costs, channel price, agent wage, or holdout','Cannot estimate incremental ROI reliably','Run randomized targeting test and collect full cost data'),
]
pd.DataFrame(issues,columns=['issue','evidence','impact','treatment']).to_csv(SUB/'data_quality_issues.csv',index=False)
# Reproducible memo and descriptive segment outputs.
(SUB/'executive_memo.md').write_text((SUB/'docs'/'executive_memo_template.md').read_text(encoding='utf-8'),encoding='utf-8')

# Descriptive current-snapshot segment cuts; these are associations, not causal effects.
seg_accounts=load('accounts',dtype={'account_id':'string'})
seg_pay=pay[pay.payment_status.eq('SUCCESS')].copy()
seg_amount=seg_pay.groupby('account_id').amount.sum().rename('gross_successful_amount')
seg_events=seg_pay.groupby('account_id').payment_id.nunique().rename('success_event_count')
seg=seg_accounts.merge(seg_amount,on='account_id',how='left').merge(seg_events,on='account_id',how='left')
seg[['gross_successful_amount','success_event_count']]=seg[['gross_successful_amount','success_event_count']].fillna(0)
seg['paid_account']=(seg.success_event_count>0).astype(int)
for dim in ['risk_segment','loan_type','timezone','status']:
    tab=seg.groupby(dim,dropna=False).agg(accounts=('account_id','nunique'),paying_accounts=('paid_account','sum'),gross_amount=('gross_successful_amount','sum')).reset_index()
    tab['payer_penetration_file_set_pct']=100*tab.paying_accounts/tab.accounts
    tab.to_csv(SUB/f'{dim}_recovery_descriptive.csv',index=False)
seg['dpd_bucket']=pd.cut(seg.dpd,[-1,0,30,60,90,180,100000],labels=['0','1-30','31-60','61-90','91-180','181+'])
tab=seg.groupby('dpd_bucket',observed=False).agg(accounts=('account_id','nunique'),paying_accounts=('paid_account','sum'),gross_amount=('gross_successful_amount','sum')).reset_index()
tab['payer_penetration_file_set_pct']=100*tab.paying_accounts/tab.accounts
tab.to_csv(SUB/'dpd_recovery_descriptive.csv',index=False)
targets=load('daily_targeting').merge(load('campaigns')[['campaign_id','strategy_version','channel','campaign_name']],on='campaign_id',how='left')
targets['account_lifetime_success_amount']=targets.account_id.map(seg_amount).fillna(0)
tab=targets.groupby(['strategy_version','channel'],dropna=False).agg(target_rows=('target_id','size'),distinct_accounts=('account_id','nunique'),associated_account_lifetime_success_amount=('account_lifetime_success_amount','sum')).reset_index()
tab['interpretation']='Association only: payments may predate or follow exposure; accounts can be targeted repeatedly.'
tab.to_csv(SUB/'targeting_exposure_descriptive.csv',index=False)
print(json.dumps({'monthly':monthly.to_dict('records'),'summary':report},indent=2,default=str))
# Additional requested-driver diagnostics (descriptive only).
attempts=load('call_attempts')
per_account=attempts.groupby('account_id').size().rename('attempt_count').reset_index()
per_account['attempt_band']=pd.cut(per_account.attempt_count,[0,2,4,6,8,10000],labels=['1-2','3-4','5-6','7-8','9+'])
attempt_dist=per_account.groupby('attempt_band',observed=False).agg(accounts=('account_id','nunique'),attempts=('attempt_count','sum')).reset_index()
attempt_dist['share_of_attempted_accounts_pct']=100*attempt_dist.accounts/per_account.account_id.nunique()
attempt_dist.to_csv(SUB/'attempt_frequency_descriptive.csv',index=False)

# Current geography is joined only through the account's borrower_id; unmatched IDs remain excluded.
borrowers_current=pd.read_csv(GOLD/'golden_borrowers_current.csv')
geo=seg_accounts.merge(borrowers_current[['borrower_id','city','state']],on='borrower_id',how='left')
geo=geo.merge(seg_amount.rename('gross_successful_amount'),on='account_id',how='left')
geo['gross_successful_amount']=geo.gross_successful_amount.fillna(0)
geo['paid_account']=(geo.gross_successful_amount>0).astype(int)
geo_out=geo.groupby('state',dropna=False).agg(accounts=('account_id','nunique'),paying_accounts=('paid_account','sum'),gross_amount=('gross_successful_amount','sum')).reset_index()
geo_out['payer_penetration_file_set_pct']=100*geo_out.paying_accounts/geo_out.accounts
geo_out.to_csv(SUB/'geography_state_descriptive.csv',index=False)

# Vendor call outcome is only an ANSWERED-status proxy, not RPC or causal vendor lift.
call_data=load('calls')
vend=call_data.groupby('vendor_id',dropna=False).agg(call_rows=('call_id','size'),distinct_call_ids=('call_id','nunique'),answered_status_rows=('call_status',lambda x:(x=='ANSWERED').sum())).reset_index()
vend['answered_status_share_pct']=100*vend.answered_status_rows/vend.call_rows
vend.to_csv(SUB/'vendor_call_status_descriptive.csv',index=False)
