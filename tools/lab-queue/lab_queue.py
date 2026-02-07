#!/usr/bin/env python3
"""
Lab Queue - lightweight task queue for security lab work.

Keeps a JSON queue of targets/experiments with notes and scope reminders,
plus Markdown export for reports. Linux CLI, zero external deps.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List

DB_PATH = Path(__file__).parent / "db.json"


@dataclass
class Item:
    id: int
    title: str
    scope: str = ""
    notes: str = ""
    severity: str = "info"
    status: str = "queued"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


def load_db(db_path: Path) -> List[Item]:
    if not db_path.exists():
        return []
    raw = json.loads(db_path.read_text())
    return [Item(**entry) for entry in raw]


def save_db(db_path: Path, items: List[Item]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text(json.dumps([asdict(i) for i in items], indent=2))


def add_item(db_path: Path, title: str, scope: str, notes: str, severity: str) -> Item:
    items = load_db(db_path)
    item = Item(id=int(time.time() * 1000), title=title, scope=scope, notes=notes, severity=severity)
    items.append(item)
    save_db(db_path, items)
    return item


def list_items(db_path: Path) -> List[Item]:
    return load_db(db_path)


def complete_item(db_path: Path, item_id: int) -> Item:
    items = load_db(db_path)
    for item in items:
        if item.id == item_id:
            item.status = "done"
            save_db(db_path, items)
            return item
    sys.exit(f"Item not found: {item_id}")


def next_item(db_path: Path) -> Item | None:
    items = load_db(db_path)
    for item in items:
        if item.status == "queued":
            return item
    return None


def export_markdown(db_path: Path, out_path: Path) -> Path:
    items = load_db(db_path)
    lines = ["# Lab queue", ""]
    if not items:
        lines.append("_No items queued._")
    for item in items:
        lines.append(f"## {item.title}")
        lines.append(f"- id: `{item.id}`")
        lines.append(f"- status: {item.status}")
        lines.append(f"- severity: {item.severity}")
        lines.append(f"- created_at: {item.created_at}")
        if item.scope:
            lines.append(f"- scope: {item.scope}")
        if item.notes:
            lines.append("")
            lines.append(item.notes)
        lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).strip() + "\n")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lab Queue - track lab tasks/targets with scope notes. "
        "Stores data in tools/lab-queue/db.json.",
    )
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Path to DB JSON (default: tools/lab-queue/db.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    add_cmd = sub.add_parser("add", help="Add a new lab item")
    add_cmd.add_argument("--title", required=True, help="Short title/target")
    add_cmd.add_argument("--scope", default="", help="Scope reminder or authorization note")
    add_cmd.add_argument("--notes", default="", help="Freeform notes")
    add_cmd.add_argument("--severity", default="info", help="info|low|med|high|critical")

    sub.add_parser("list", help="List all items")
    sub.add_parser("next", help="Show next queued item")

    complete_cmd = sub.add_parser("done", help="Mark an item done")
    complete_cmd.add_argument("--id", type=int, required=True, help="Item ID")

    export_cmd = sub.add_parser("export", help="Export queue to Markdown")
    export_cmd.add_argument("--out", type=Path, default=Path("tools/lab-queue/queue.md"), help="Markdown output path")

    args = parser.parse_args()
    db_path: Path = args.db

    if args.command == "add":
        item = add_item(db_path, args.title, args.scope, args.notes, args.severity)
        print(f"[+] Added {item.title} (id={item.id})")
    elif args.command == "list":
        for item in list_items(db_path):
            print(f"{item.id} [{item.status}] ({item.severity}) {item.title}  scope={item.scope or '-'}")
    elif args.command == "next":
        item = next_item(db_path)
        if item:
            print(f"{item.id} [{item.status}] ({item.severity}) {item.title}  scope={item.scope or '-'}")
        else:
            print("Queue empty.")
    elif args.command == "done":
        item = complete_item(db_path, args.id)
        print(f"[+] Marked done: {item.title} (id={item.id})")
    elif args.command == "export":
        out_path = export_markdown(db_path, args.out)
        print(f"[+] Exported Markdown -> {out_path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
