import re
import subprocess
import time


_USB_SCAN_CACHE = {
    "timestamp": 0.0,
    "items": [],
}

_USB_TARGET_SCAN_CACHE = {
    "timestamp": 0.0,
    "items": [],
    "target_signature": (),
}


FAST_USB_COMMANDS = [
    (
        "WMIC",
        ["wmic", "path", "Win32_USBControllerDevice", "get", "Dependent"],
    ),
    (
        "PNPUTIL",
        ["pnputil", "/enum-devices", "/connected"],
    ),
]

SLOW_USB_COMMANDS = [
    (
        "CIM (WindowsPowerShell)",
        [
            "powershell",
            "-NoLogo",
            "-NonInteractive",
            "-NoProfile",
            "-Command",
            "Get-CimInstance -ClassName Win32_PnPEntity -Filter \"PNPDeviceID LIKE 'USB%VID_%PID_%'\" | "
            "Select-Object -ExpandProperty PNPDeviceID",
        ],
    ),
    (
        "PNP (WindowsPowerShell)",
        [
            "powershell",
            "-NoLogo",
            "-NonInteractive",
            "-NoProfile",
            "-Command",
            "Get-PnpDevice -PresentOnly -Class USB | Select-Object -ExpandProperty InstanceId",
        ],
    ),
]


def _parse_usb_ids(raw_text):
    matches = re.findall(r"USB\\VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", raw_text.upper())
    seen = set()
    items = []
    for vid, pid in matches:
        normalized = f"USB\\VID_{vid}&PID_{pid}"
        if normalized not in seen:
            seen.add(normalized)
            items.append(normalized)
    return items


def _merge_unique(primary_list, secondary_list):
    merged = []
    seen = set()
    for entry in primary_list + secondary_list:
        if entry not in seen:
            seen.add(entry)
            merged.append(entry)
    return merged


def _build_usb_device_list_with_commands(commands, command_timeout_seconds, collect_all_methods, verbose):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    def run_command(command):
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            check=False,
            timeout=command_timeout_seconds,
        )
        if result.returncode != 0:
            return ""
        return result.stdout or ""

    merged = []
    seen = set()
    for method, command in commands:
        try:
            output = run_command(command)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            if verbose:
                print(f"[USB] Enumeration method: {method} (not available or timed out)")
            continue

        usb_ids = _parse_usb_ids(output)
        if usb_ids:
            if verbose:
                print(f"[USB] Enumeration method: {method} (found {len(usb_ids)})")

            if collect_all_methods:
                for entry in usb_ids:
                    if entry not in seen:
                        seen.add(entry)
                        merged.append(entry)
                continue

            if verbose:
                print(f"[USB] Enumeration method: {method}")
            return usb_ids

        if verbose:
            print(f"[USB] Enumeration method: {method} (no USB VID/PID entries)")

    if collect_all_methods and merged:
        return merged
    return []


def build_usb_device_list(collect_all_methods=False, verbose=False):
    command_timeout_seconds = 20 if collect_all_methods else 5
    commands = FAST_USB_COMMANDS + SLOW_USB_COMMANDS
    usb_ids = _build_usb_device_list_with_commands(
        commands,
        command_timeout_seconds=command_timeout_seconds,
        collect_all_methods=collect_all_methods,
        verbose=verbose,
    )
    if collect_all_methods and verbose and usb_ids:
        print(f"[USB] Enumeration method: merged ({len(usb_ids)} entries)")
    if verbose and not usb_ids:
        print("[USB] Enumeration method: none (no USB VID/PID entries found)")
    return usb_ids


def build_usb_device_list_cached(cache_ttl_seconds=4.0, collect_all_methods=False, verbose=False):
    now = time.time()
    age = now - _USB_SCAN_CACHE["timestamp"]
    if age < cache_ttl_seconds:
        return list(_USB_SCAN_CACHE["items"])

    items = build_usb_device_list(
        collect_all_methods=collect_all_methods,
        verbose=verbose,
    )
    _USB_SCAN_CACHE["timestamp"] = now
    _USB_SCAN_CACHE["items"] = list(items)
    return items


def _has_any_target_match(usb_device_list, target_devices):
    if not target_devices:
        return bool(usb_device_list)

    vid_to_pids = build_vid_to_pids_map(usb_device_list)
    for target in target_devices:
        if len(target) == 2:
            vid, pid = target
            allow_vid_only = False
        else:
            vid, pid, allow_vid_only = target

        present, _, _ = evaluate_usb_device_match(
            usb_device_list,
            vid,
            pid,
            allow_vid_only=allow_vid_only,
            vid_to_pids=vid_to_pids,
        )
        if present:
            return True
    return False


def build_usb_device_list_fast_then_slow(target_devices=None, verbose=False):
    fast_usb_ids = _build_usb_device_list_with_commands(
        FAST_USB_COMMANDS,
        command_timeout_seconds=3,
        collect_all_methods=True,
        verbose=verbose,
    )

    if _has_any_target_match(fast_usb_ids, target_devices):
        if verbose:
            print(f"[USB] Fast scan satisfied target(s) with {len(fast_usb_ids)} entries")
        return fast_usb_ids

    if verbose:
        print("[USB] Fast scan found no target device. Falling back to slower methods...")

    slow_usb_ids = _build_usb_device_list_with_commands(
        SLOW_USB_COMMANDS,
        command_timeout_seconds=3,
        collect_all_methods=True,
        verbose=verbose,
    )
    merged = _merge_unique(fast_usb_ids, slow_usb_ids)
    if verbose:
        print(f"[USB] Fast+slow merged entries: {len(merged)}")
    return merged


def build_usb_device_list_fast_only(verbose=False):
    usb_ids = _build_usb_device_list_with_commands(
        FAST_USB_COMMANDS,
        command_timeout_seconds=3,
        collect_all_methods=True,
        verbose=verbose,
    )
    if verbose:
        print(f"[USB] Fast-only entries: {len(usb_ids)}")
    return usb_ids


def build_usb_device_list_fast_then_slow_cached(cache_ttl_seconds=4.0, target_devices=None, verbose=False):
    target_signature = tuple(target_devices or [])
    now = time.time()
    age = now - _USB_TARGET_SCAN_CACHE["timestamp"]
    if age < cache_ttl_seconds and _USB_TARGET_SCAN_CACHE["target_signature"] == target_signature:
        return list(_USB_TARGET_SCAN_CACHE["items"])

    items = build_usb_device_list_fast_then_slow(target_devices=target_devices, verbose=verbose)
    _USB_TARGET_SCAN_CACHE["timestamp"] = now
    _USB_TARGET_SCAN_CACHE["items"] = list(items)
    _USB_TARGET_SCAN_CACHE["target_signature"] = target_signature
    return items


def is_device_in_usb_list(usb_device_list, vid, pid):
    vid_pid = f"VID_{vid}&PID_{pid}".upper()
    return any(vid_pid in entry for entry in usb_device_list)


def parse_vid_pid_entries(usb_device_list):
    pairs = []
    for entry in usb_device_list:
        match = re.search(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", entry.upper())
        if match:
            pairs.append((match.group(1), match.group(2), entry))
    return pairs


def build_vid_to_pids_map(usb_device_list):
    vid_to_pids = {}
    for vid, pid, _ in parse_vid_pid_entries(usb_device_list):
        if vid not in vid_to_pids:
            vid_to_pids[vid] = set()
        vid_to_pids[vid].add(pid)
    return vid_to_pids


def evaluate_usb_device_match(usb_device_list, vid, pid, allow_vid_only=False, vid_to_pids=None):
    vid_upper = str(vid).upper()
    pid_upper = str(pid).upper()

    if vid_to_pids is None:
        vid_to_pids = build_vid_to_pids_map(usb_device_list)

    matched_pids = sorted(vid_to_pids.get(vid_upper, set()))
    if pid_upper in matched_pids:
        return True, "exact", matched_pids

    if matched_pids:
        if allow_vid_only:
            return True, "vid_only", matched_pids
        return False, "vid_mismatch", matched_pids

    return False, "vid_missing", []
