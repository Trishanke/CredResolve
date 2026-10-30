#!/usr/bin/env python3
"""Conservative, reproducible preprocessing for the collections assignment data.

Raw inputs are read-only. Cleaned staging tables and exact-duplicate quarantine files
are written under output/preprocessed/. No business-level deduplication, imputation,
timezone conversion, payment attribution, or entity merging is performed here.
"""
from __future__ import annotations
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "collections_30k_dataset (1)"
OUTPUT = ROOT / "output" / "preprocessed"
QUARANTINE = OUTPUT / "quarantine"

PRIMARY_KEYS = {
    "borrowers": "borrower_id", "accounts": "account_id", "agents": "agent_id",
    "agent_sessions": "session_id", "campaigns": "campaign_id", "daily_targeting": "target_id",
    "calls": "call_id", "call_attempts": "attempt_id", "call_dispositions": "disposition_id",
    "whatsapp_events": "whatsapp_event_id", "sms_events": "sms_event_id",
    "field_visits": "visit_id", "promises_to_pay": "ptp_id", "payments": "payment_id",
    "vendor_telephony": "vendor_id", "complaints": "complaint_id",
    "account_status_history": "history_id",
}
FOREIGN_KEYS = {
    "accounts": {"borrower_id": "borrowers.borrower_id"},
    "agent_sessions": {"agent_id": "agents.agent_id"},
    "daily_targeting": {"account_id": "accounts.account_id", "campaign_id": "campaigns.campaign_id"},
    "calls": {"account_id": "accounts.account_id", "borrower_id": "borrowers.borrower_id", "agent_id": "agents.agent_id", "campaign_id": "campaigns.campaign_id", "vendor_id": "vendor_telephony.vendor_id"},
    "call_attempts": {"account_id": "accounts.account_id", "borrower_id": "borrowers.borrower_id", "call_id": "calls.call_id", "agent_id": "agents.agent_id", "vendor_id": "vendor_telephony.vendor_id"},
    "call_dispositions": {"account_id": "accounts.account_id", "borrower_id": "borrowers.borrower_id", "call_id": "calls.call_id", "agent_id": "agents.agent_id"},
    "whatsapp_events": {"account_id": "accounts.account_id", "borrower_id": "borrowers.borrower_id", "provider_id": "vendor_telephony.vendor_id"},
    "sms_events": {"account_id": "accounts.account_id", "borrower_id": "borrowers.borrower_id", "provider_id": "vendor_telephony.vendor_id"},
    "field_visits": {"account_id": "accounts.account_id", "borrower_id": "borrowers.borrower_id", "agent_id": "agents.agent_id"},
    "promises_to_pay": {"account_id": "accounts.account_id", "borrower_id": "borrowers.borrower_id", "agent_id": "agents.agent_id"},
    "payments": {"account_id": "accounts.account_id", "borrower_id": "borrowers.borrower_id"},
    "complaints": {"account_id": "accounts.account_id", "borrower_id": "borrowers.borrower_id"},
    "account_status_history": {"account_id": "accounts.account_id", "borrower_id": "borrowers.borrower_id"},
}


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def clean_scalar(value: str | None) -> str:
    return (value or "").strip()


def parse_typed(value: str, dtype: str):
    """Return value normalized to a safe CSV string; never infer missing values."""
    if value == "":
        return "", None
    try:
        if dtype.startswith("datetime"):
            # Validate only. Keep the source wall-clock value; timezone is separately
            # supplied/inconsistent, so silently converting would invent semantics.
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return value, None
        if dtype in ("int64", "Int64"):
            return str(int(value)), None
        if dtype.startswith("float"):
            number = float(value)
            if number != number or number in (float("inf"), float("-inf")):
                raise ValueError("non-finite numeric")
            return format(number, ".15g"), None
    except (ValueError, OverflowError):
        return "", f"invalid {dtype}: {value}"
    return value, None


def main():
    if not INPUT.is_dir():
        raise SystemExit(f"Input dataset directory not found: {INPUT}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    QUARANTINE.mkdir(parents=True, exist_ok=True)

    dictionary_path = INPUT / "data_dictionary.csv"
    _, dictionary_rows = read_csv(dictionary_path)
    types = {(r.get("dataset", ""), r.get("column", "")): r.get("dtype", "object") for r in dictionary_rows}

    tables = {}
    for path in sorted(INPUT.glob("*.csv")):
        table = path.stem
        header, rows = read_csv(path)
        tables[table] = (header, rows)

    known_keys = {}
    for table, (header, rows) in tables.items():
        key = PRIMARY_KEYS.get(table)
        if key and key in header:
            known_keys[f"{table}.{key}"] = {clean_scalar(r.get(key)) for r in rows if clean_scalar(r.get(key))}

    report = {
        "input_directory": str(INPUT), "output_directory": str(OUTPUT),
        "policy": [
            "Trim leading/trailing whitespace in every field; blank/whitespace-only becomes null (empty CSV field).",
            "Parse numeric fields using data_dictionary.csv; invalid values become null and are written to quarantine with reason.",
            "Validate datetime syntax but preserve original timestamp text and timezone context; no timezone localization/conversion.",
            "Remove exact duplicate rows only; preserve removed copies in quarantine.",
            "Retain conflicting duplicate identifiers and repeated entity snapshots; flag them in the report for later business adjudication.",
            "Do not impute missing data, merge entities, deduplicate payments by reference, attribute payments, or filter business rows.",
            "Add source_file and source_row_number columns for lineage."
        ],
        "tables": {}, "foreign_key_checks": [],
        "limitations": ["Dataset spans less than 12 months based on initial profile; this pipeline does not infer missing history.", "Timestamps may be UTC, Asia/Kolkata, or Asia/Dubai without reliable per-row timezone semantics."]
    }

    for table, (header, rows) in tables.items():
        source = INPUT / f"{table}.csv"
        clean_rows = []
        removed_exact = []
        invalid_values = []
        seen = set()
        missing = Counter()
        for rownum, row in enumerate(rows, start=2):
            cleaned = {}
            row_errors = []
            for col in header:
                raw = clean_scalar(row.get(col))
                dtype = types.get((table, col), "object")
                val, err = parse_typed(raw, dtype)
                cleaned[col] = val
                if val == "": missing[col] += 1
                if err: row_errors.append((col, err))
            # Equality uses the cleaned source columns, before lineage fields.
            signature = tuple(cleaned.get(c, "") for c in header)
            if signature in seen:
                removed_exact.append({**cleaned, "source_file": source.name, "source_row_number": rownum, "quarantine_reason": "exact_duplicate_after_trim_and_type_normalization"})
                continue
            seen.add(signature)
            clean_rows.append({**cleaned, "source_file": source.name, "source_row_number": rownum})
            for col, err in row_errors:
                invalid_values.append({**cleaned, "source_file": source.name, "source_row_number": rownum, "quarantine_reason": f"{col}: {err}"})

        out_fields = header + ["source_file", "source_row_number"]
        outpath = OUTPUT / f"{table}.csv"
        with outpath.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
            w.writeheader(); w.writerows(clean_rows)
        qfields = header + ["source_file", "source_row_number", "quarantine_reason"]
        if removed_exact:
            with (QUARANTINE / f"{table}_exact_duplicates.csv").open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=qfields); w.writeheader(); w.writerows(removed_exact)
        if invalid_values:
            with (QUARANTINE / f"{table}_invalid_values.csv").open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=qfields); w.writeheader(); w.writerows(invalid_values)

        key = PRIMARY_KEYS.get(table)
        key_values = [clean_scalar(r.get(key)) for r in rows if key and clean_scalar(r.get(key))]
        key_counts = Counter(key_values)
        duplicate_key_rows = sum(n - 1 for n in key_counts.values() if n > 1)
        duplicate_key_values = sum(1 for n in key_counts.values() if n > 1)
        report["tables"][table] = {
            "input_rows": len(rows), "clean_rows": len(clean_rows),
            "exact_duplicate_rows_removed_to_quarantine": len(removed_exact),
            "invalid_typed_values_to_quarantine": len(invalid_values),
            "missing_by_column_after_trim": dict(missing),
            "primary_key_candidate": key,
            "duplicate_primary_key_values": duplicate_key_values,
            "extra_rows_sharing_primary_key": duplicate_key_rows,
            "cleaned_file": str(outpath),
        }

    # FK checks use the source key sets, preserving all rows and flagging unmatched values.
    for table, relations in FOREIGN_KEYS.items():
        if table not in tables: continue
        _, rows = tables[table]
        for col, target in relations.items():
            target_keys = known_keys.get(target, set())
            nonempty = [clean_scalar(r.get(col)) for r in rows if clean_scalar(r.get(col))]
            unmatched = sum(v not in target_keys for v in nonempty)
            report["foreign_key_checks"].append({"source": f"{table}.{col}", "target": target, "nonempty_values": len(nonempty), "unmatched_values": unmatched, "action": "flag only; rows retained"})

    with (OUTPUT / "preprocessing_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    with (OUTPUT / "preprocessing_report.md").open("w", encoding="utf-8") as f:
        f.write("# Preprocessing report\n\n")
        f.write("This is a conservative staging cleanup, not a final golden dataset. Raw files are unchanged.\n\n")
        f.write("## Rules applied\n\n")
        for rule in report["policy"]: f.write(f"- {rule}\n")
        f.write("\n## Table results\n\n| Table | Input | Clean | Exact duplicates quarantined | Invalid typed values | Duplicate PK values | Missing fields |\n|---|---:|---:|---:|---:|---:|---|\n")
        for table, s in report["tables"].items():
            f.write(f"| {table} | {s['input_rows']} | {s['clean_rows']} | {s['exact_duplicate_rows_removed_to_quarantine']} | {s['invalid_typed_values_to_quarantine']} | {s['duplicate_primary_key_values']} | {', '.join(f'{k}: {v}' for k,v in s['missing_by_column_after_trim'].items()) or 'None'} |\n")
        f.write("\n## Foreign key checks\n\n| Source | Target | Nonempty | Unmatched |\n|---|---|---:|---:|\n")
        for x in report["foreign_key_checks"]: f.write(f"| {x['source']} | {x['target']} | {x['nonempty_values']} | {x['unmatched_values']} |\n")
        f.write("\n## Interpretation and next decisions\n\n")
        f.write("Exact duplicate rows are excluded from staging and retained in quarantine. Repeated IDs with differing row content remain in cleaned tables; in particular, agent and borrower records require snapshot/entity-resolution logic before choosing a canonical record. Missing values remain null because no authoritative imputation rules were supplied. Payment references are not used as a deduplication key: successful/reversed status and transaction lineage need adjudication. Event timestamps are validated but not converted because source timezone semantics vary.\n")
        f.write("\nThis report does not claim the 11% recovery change, establish causal drivers, or produce account-level golden facts. Those require explicit denominator, payment reconciliation, event attribution, and snapshot rules.\n")

if __name__ == "__main__":
    main()
