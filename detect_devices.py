import argparse
import platform
import sys

from usb_detection import (
    build_usb_device_list,
    build_usb_device_list_fast_only,
    build_usb_device_list_fast_then_slow,
    build_vid_to_pids_map,
    evaluate_usb_device_match,
)
from log_utils import init_log_session, get_log_file_path


KNOWN_DEVICES = [
    ("saleae", "Saleae Logic", "21A9", "1006", True),
    ("ellisys", "Ellisys C-Tracker", "1500", "0600", True),
    ("cy4500", "CY4500", "04B4", "F67E", False),
    ("cy4500epr", "CY4500 EPR", "04B4", "FDEF", False),
]
def parse_args():
    parser = argparse.ArgumentParser(
        description="Standalone USB detector for Saleae/Ellisys/CY4500 devices."
    )
    parser.add_argument(
        "--all-methods",
        action="store_true",
        help="Force merge results from all supported methods (slowest but most comprehensive).",
    )
    parser.add_argument(
        "--fast-device-check",
        action="store_true",
        help="Use fast USB checks only and skip slower fallback methods.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-method diagnostics during enumeration.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print full normalized USB VID/PID list.",
    )
    parser.add_argument(
        "--require",
        choices=[entry[0] for entry in KNOWN_DEVICES],
        nargs="+",
        help="Fail with exit code 1 if any required device is not detected.",
    )
    parser.add_argument(
        "--vid-summary",
        action="store_true",
        help="Print VID to PID summary to troubleshoot PID mismatches.",
    )
    return parser.parse_args()


def main():
    init_log_session(script_name="detect_devices.py")
    args = parse_args()
    print(f"[LOG] Writing diagnostics to: {get_log_file_path()}")

    print(f"[SYS] Platform: {platform.platform()}")
    print(f"[SYS] Python: {sys.version.split()[0]}")

    target_devices = [(vid, pid, allow_vid_only) for _, _, vid, pid, allow_vid_only in KNOWN_DEVICES]

    if args.fast_device_check:
        usb_list = build_usb_device_list_fast_only(verbose=args.verbose)
    elif args.all_methods:
        usb_list = build_usb_device_list(collect_all_methods=True, verbose=args.verbose)
    else:
        usb_list = build_usb_device_list_fast_then_slow(
            target_devices=target_devices,
            verbose=args.verbose,
        )

    print(f"[USB] Normalized USB VID/PID entries: {len(usb_list)}")

    vid_to_pids = build_vid_to_pids_map(usb_list)

    if args.list:
        if usb_list:
            print("[USB] Device list start")
            for index, entry in enumerate(usb_list, start=1):
                print(f"[USB] {index:03d}: {entry}")
            print("[USB] Device list end")
        else:
            print("[USB] No USB entries found.")

    if args.vid_summary:
        if vid_to_pids:
            print("[USB] VID summary start")
            for vid in sorted(vid_to_pids.keys()):
                pid_list = ", ".join(sorted(vid_to_pids[vid]))
                print(f"[USB] VID_{vid}: PID(s) {pid_list}")
            print("[USB] VID summary end")
        else:
            print("[USB] VID summary: no VID/PID pairs found.")

    status_map = {}
    print("[CHECK] Known device status")
    for key, display_name, vid, pid, allow_vid_only in KNOWN_DEVICES:
        present, reason, matched_pids = evaluate_usb_device_match(
            usb_list,
            vid,
            pid,
            allow_vid_only=allow_vid_only,
            vid_to_pids=vid_to_pids,
        )
        status_map[key] = present
        if present:
            print(f"[CHECK] {display_name} ({vid}:{pid}): FOUND")
            continue

        if reason == "vid_mismatch":
            pid_list = ", ".join(matched_pids)
            print(
                f"[CHECK] {display_name} ({vid}:{pid}): NOT FOUND (VID matched, different PID(s): {pid_list})"
            )
        else:
            print(f"[CHECK] {display_name} ({vid}:{pid}): NOT FOUND (VID not present)")

    if args.require:
        missing = [key for key in args.require if not status_map.get(key, False)]
        if missing:
            print(f"[RESULT] Missing required device(s): {', '.join(missing)}")
            return 1

    print("[RESULT] Device detection script completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
