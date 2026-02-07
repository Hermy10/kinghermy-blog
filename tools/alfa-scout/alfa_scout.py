#!/usr/bin/env python3
"""
Alfa Scout - field Wi-Fi helper for the Alfa AWUS036ACM.

Linux-only CLI that leans on system tools (iw, ip, nmcli, tshark/aircrack-ng)
for surveys and authorized captures. Use on networks you own or are permitted
to test.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple


def run_cmd(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a command and return the completed process."""
    return subprocess.run(
        cmd,
        check=check,
        capture_output=True,
        text=True,
    )


def ensure_bins(binaries: Iterable[str]) -> None:
    missing = [b for b in binaries if shutil.which(b) is None]
    if missing:
        sys.exit(f"Missing required binaries: {', '.join(missing)}")


def parse_scan_output(scan_output: str) -> List[dict]:
    """Parse `iw dev <iface> scan` output into a lightweight list."""
    networks = []
    current: dict = {}
    for raw_line in scan_output.splitlines():
        line = raw_line.strip()
        if line.startswith("BSS "):
            if current:
                networks.append(current)
            current = {"bssid": line.split()[1].strip("()")}
        elif line.startswith("freq:"):
            current["freq_mhz"] = int(line.split("freq:")[1].strip())
        elif line.startswith("signal:"):
            signal_value = line.split("signal:")[1].split()[0]
            current["signal_dbm"] = float(signal_value)
        elif line.startswith("SSID:"):
            current["ssid"] = line.split("SSID:")[1].strip()
        elif line.startswith("DS Parameter set: channel "):
            channel = line.split("channel ")[1].strip()
            current["channel"] = int(channel)
        elif line.startswith("capability:"):
            current["capability"] = line.split("capability:")[1].strip()
        elif line.startswith("RSN:"):
            current.setdefault("security", set()).add("RSN")
        elif line.startswith("WPA:"):
            current.setdefault("security", set()).add("WPA")
        elif line.startswith("WEP:"):
            current.setdefault("security", set()).add("WEP")
    if current:
        networks.append(current)
    # convert any sets to sorted lists for JSON safety
    for net in networks:
        if isinstance(net.get("security"), set):
            net["security"] = sorted(net["security"])
    return networks


def list_ifaces() -> List[dict]:
    """Return wireless interfaces from `iw dev`."""
    ensure_bins(["iw"])
    proc = run_cmd(["iw", "dev"])
    ifaces = []
    current: dict = {}
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if line.startswith("Interface"):
            if current:
                ifaces.append(current)
            current = {"name": line.split()[1]}
        elif line.startswith("type") and current:
            current["type"] = line.split()[1]
        elif line.startswith("channel") and current:
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                current["channel"] = int(parts[1])
        elif line.startswith("txpower") and current:
            current["txpower_dbm"] = line.split()[1]
    if current:
        ifaces.append(current)
    return ifaces


def survey(iface: str, outfile: Path) -> Tuple[int, Path]:
    ensure_bins(["iw"])
    scan = run_cmd(["iw", "dev", iface, "scan"])
    networks = parse_scan_output(scan.stdout)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "captured_at": datetime.utcnow().isoformat() + "Z",
        "iface": iface,
        "networks": networks,
    }
    outfile.write_text(json.dumps(payload, indent=2))
    return len(networks), outfile


def iface_status(iface: str) -> str:
    ensure_bins(["iw"])
    info = run_cmd(["iw", "dev", iface, "info"])
    return info.stdout


def set_monitor_mode(iface: str, enabled: bool) -> None:
    ensure_bins(["ip", "iw"])
    state = "monitor" if enabled else "managed"
    cmds = [
        ["sudo", "ip", "link", "set", iface, "down"],
        ["sudo", "iw", "dev", iface, "set", "type", state],
        ["sudo", "ip", "link", "set", iface, "up"],
    ]
    for cmd in cmds:
        run_cmd(cmd)


def capture_handshake(
    iface: str,
    outfile: Path,
    seconds: int,
    channel: int | None,
    bssid: str | None,
) -> Path:
    ensure_bins(["tshark"])
    outfile.parent.mkdir(parents=True, exist_ok=True)
    if channel:
        run_cmd(["sudo", "iw", "dev", iface, "set", "channel", str(channel)])

    capture_cmd = ["sudo", "tshark", "-I", "-i", iface, "-w", str(outfile), "-a", f"duration:{seconds}"]
    if bssid:
        capture_cmd += ["-f", f"wlan host {bssid}"]
    print(f"[+] Capturing for {seconds}s on {iface} -> {outfile}")
    try:
        subprocess.run(capture_cmd, check=True)
    except subprocess.CalledProcessError as err:
        sys.exit(f"Capture failed: {err}")
    return outfile


def render_markdown_report(survey_json: Path, markdown_out: Path) -> Path:
    if not survey_json.exists():
        sys.exit(f"Survey file not found: {survey_json}")
    data = json.loads(survey_json.read_text())
    networks = data.get("networks", [])
    sorted_nets = sorted(
        networks, key=lambda n: n.get("signal_dbm", -999), reverse=True
    )[:10]
    lines = [
        f"# Alfa Scout survey report",
        f"- captured_at: {data.get('captured_at', 'unknown')}",
        f"- iface: {data.get('iface', 'unknown')}",
        "",
        "## Top networks by signal",
        "| SSID | BSSID | Channel | Signal (dBm) | Security |",
        "| --- | --- | --- | --- | --- |",
    ]
    for net in sorted_nets:
        lines.append(
            f"| {net.get('ssid','(hidden)')} | {net.get('bssid','?')} | "
            f"{net.get('channel','?')} | {net.get('signal_dbm','?')} | "
            f"{'/'.join(net.get('security',[]) or ['?'])} |"
        )
    report = "\n".join(lines) + "\n"
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(report)
    return markdown_out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Alfa Scout - Wi-Fi helper for the Alfa AWUS036ACM (Linux). "
        "Use only on networks you own or are authorized to test.",
    )
    parser.add_argument("--iface", default="wlan0", help="Wireless interface (default: wlan0)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show interface status (iw info)")
    sub.add_parser("list-ifaces", help="List wireless interfaces (iw dev)")

    sub.add_parser("monitor-on", help="Switch interface to monitor mode")
    sub.add_parser("monitor-off", help="Switch interface back to managed mode")

    survey_parser = sub.add_parser("survey", help="Run a scan and write JSON results")
    survey_parser.add_argument(
        "--out",
        type=Path,
        default=Path("tools/alfa-scout/reports/survey.json"),
        help="Output JSON path",
    )

    capture_parser = sub.add_parser("capture", help="Capture an authorized handshake/traffic sample")
    capture_parser.add_argument(
        "--out",
        type=Path,
        default=Path("tools/alfa-scout/reports/handshake.pcapng"),
        help="Capture file path",
    )
    capture_parser.add_argument("--seconds", type=int, default=45, help="Capture duration in seconds")
    capture_parser.add_argument("--channel", type=int, help="Set channel before capture")
    capture_parser.add_argument("--bssid", help="Target BSSID filter to narrow capture")

    report_parser = sub.add_parser("report", help="Render a Markdown report from a survey JSON")
    report_parser.add_argument(
        "--in",
        dest="report_in",
        type=Path,
        default=Path("tools/alfa-scout/reports/survey.json"),
        help="Survey JSON input path",
    )
    report_parser.add_argument(
        "--out",
        dest="report_out",
        type=Path,
        default=Path("tools/alfa-scout/reports/survey.md"),
        help="Markdown report output path",
    )

    args = parser.parse_args()

    if args.command == "status":
        print(iface_status(args.iface))
    elif args.command == "list-ifaces":
        for iface in list_ifaces():
            print(
                f"{iface.get('name')}  type={iface.get('type','?')}  "
                f"channel={iface.get('channel','?')}  txpower={iface.get('txpower_dbm','?')}"
            )
    elif args.command == "monitor-on":
        set_monitor_mode(args.iface, enabled=True)
        print(f"[+] {args.iface} set to monitor mode.")
    elif args.command == "monitor-off":
        set_monitor_mode(args.iface, enabled=False)
        print(f"[+] {args.iface} set to managed mode.")
    elif args.command == "survey":
        count, path = survey(args.iface, args.out)
        print(f"[+] Survey complete: {count} networks -> {path}")
    elif args.command == "capture":
        path = capture_handshake(args.iface, args.out, args.seconds, args.channel, args.bssid)
        print(f"[+] Capture saved to {path}")
    elif args.command == "report":
        out_path = render_markdown_report(args.report_in, args.report_out)
        print(f"[+] Markdown report written to {out_path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
