"""Reads client_audit.csv exactly as the client delivered it."""

import csv
from dataclasses import dataclass

from .settings import CLIENT_AUDIT_CSV


@dataclass
class AuditRow:
    row: int
    page_url: str
    image_url: str
    note: str


def read_client_audit():
    with open(CLIENT_AUDIT_CSV, newline="", encoding="utf-8") as f:
        return [AuditRow(int(r["row"]), r["page_url"].strip(), r["image_url"].strip(),
                         r["auditor_note"]) for r in csv.DictReader(f)]
