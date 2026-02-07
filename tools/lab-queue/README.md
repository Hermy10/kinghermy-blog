# Lab Queue (Linux CLI)

Lightweight queue for lab/engagement tasks with scope reminders. Stores JSON at `tools/lab-queue/db.json` and can export Markdown for reports.

## Quickstart

```bash
cd tools/lab-queue
python3 lab_queue.py add --title "Audit guest Wi-Fi" --scope "Office lab only" --severity high --notes "Check captive portal + rate limiting"
python3 lab_queue.py list
python3 lab_queue.py next
python3 lab_queue.py done --id <id>
python3 lab_queue.py export --out queue.md
```

## Commands

- `add` — create a queue item with title, scope, severity, notes.
- `list` — show all items.
- `next` — show the first queued item.
- `done` — mark an item complete by id.
- `export` — write a Markdown snapshot of the queue.

Data is plain JSON; feel free to sync it with git or back it up. Use scope fields to keep authorization front and center.
