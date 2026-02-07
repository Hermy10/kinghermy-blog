# Alfa Scout (Linux CLI)

Field Wi-Fi helper for the Alfa AWUS036ACM. Uses system tools (`iw`, `ip`, `tshark`, `nmcli`) to flip monitor mode, run surveys, and capture authorized handshakes or traffic snapshots. Use only on networks you own or are permitted to test.

## Prereqs

- Linux with the Alfa AWUS036ACM attached
- Packages: `iw`, `iproute2`, `tshark` (or Wireshark), `nmcli` (NetworkManager)
- Python 3.10+
- Sudo privileges for monitor mode and captures

## Quickstart

```bash
cd tools/alfa-scout
python3 alfa_scout.py status --iface wlan0
python3 alfa_scout.py monitor-on --iface wlan0
python3 alfa_scout.py survey --iface wlan0 --out reports/survey.json
# Optional: set channel to your authorized target and capture a short sample
python3 alfa_scout.py capture --iface wlan0 --channel 6 --seconds 45 --bssid <target-bssid> --out reports/handshake.pcapng
python3 alfa_scout.py monitor-off --iface wlan0
```

Outputs land in `tools/alfa-scout/reports/` by default.

## Commands

- `status` — show interface details (`iw dev <iface> info`).
- `list-ifaces` — list wireless interfaces from `iw dev`.
- `monitor-on` / `monitor-off` — toggle monitor mode with `iw`/`ip`.
- `survey` — run `iw dev <iface> scan`, parse results, and save JSON.
- `capture` — run a timed `tshark` capture (promiscuous/monitor) with optional channel + BSSID filter.
- `report` — render a Markdown summary from a survey JSON (top networks by signal).

## Notes

- Keep captures within scope; this is for authorized testing only.
- If NetworkManager keeps resetting the interface, temporarily stop it while capturing: `sudo systemctl stop NetworkManager` (remember to start it again afterwards).
- For deeper analysis, open the saved PCAPNG in Wireshark or feed the JSON survey into your reporting workflow.
