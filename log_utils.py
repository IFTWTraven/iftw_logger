from datetime import datetime
import builtins
import os
import re
import sys
import threading


_LOG_STATE = {
    "initialized": False,
    "log_date": "",
    "logs_dir": "",
    "log_index": 0,
    "log_file": "",
    "max_bytes": 10 * 1024 * 1024,
    "session_id": "",
    "script_name": "",
}
_LOCK = threading.RLock()
_ORIGINAL_PRINT = builtins.print
_ORIGINAL_STDOUT = sys.stdout
_TIMESTAMP_PREFIX_RE = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]")


def _now():
    return datetime.now()


def _safe_int(value, default_value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default_value


def _build_log_path(logs_dir, date_str, index):
    if index <= 0:
        return os.path.join(logs_dir, f"{date_str}.txt")
    return os.path.join(logs_dir, f"{date_str}_{index:02d}.txt")


def _find_latest_daily_index(logs_dir, date_str):
    pattern = re.compile(rf"^{date_str}(?:_(\d{{2}}))?\.txt$")
    highest_index = -1
    for name in os.listdir(logs_dir):
        match = pattern.match(name)
        if not match:
            continue
        if match.group(1) is None:
            index = 0
        else:
            index = _safe_int(match.group(1), 0)
        if index > highest_index:
            highest_index = index
    return highest_index


def _ensure_current_file(date_str, logs_dir, max_bytes):
    latest_index = _find_latest_daily_index(logs_dir, date_str)
    if latest_index < 0:
        return 0

    candidate = _build_log_path(logs_dir, date_str, latest_index)
    try:
        current_size = os.path.getsize(candidate)
    except OSError:
        current_size = 0

    if current_size >= max_bytes:
        return latest_index + 1
    return latest_index


def _daily_log_file(base_dir=None):
    work_dir = base_dir or os.getcwd()
    date_str = _now().strftime("%Y%m%d")
    logs_dir = os.path.join(work_dir, date_str)
    os.makedirs(logs_dir, exist_ok=True)
    max_mb = _safe_int(os.environ.get("S2A_LOG_MAX_MB", "10"), 10)
    max_bytes = max(1, max_mb) * 1024 * 1024
    index = _ensure_current_file(date_str, logs_dir, max_bytes)
    return logs_dir, date_str, index, _build_log_path(logs_dir, date_str, index), max_bytes


def _write_direct(text):
    with open(_LOG_STATE["log_file"], "a", encoding="utf-8") as f:
        f.write(text)


def _rollover_header():
    ts = _now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        "",
        "-" * 88,
        f"LOG ROLLOVER | time={ts} | script={_LOG_STATE['script_name']} | session={_LOG_STATE['session_id']}",
        "-" * 88,
    ]


def _channel_setup_header():
    return [
        "CHANNEL SETUP",
        "=" * 88,
    ]


def _rotate_if_needed(additional_bytes=0):
    try:
        current_size = os.path.getsize(_LOG_STATE["log_file"])
    except OSError:
        current_size = 0

    if current_size + additional_bytes <= _LOG_STATE["max_bytes"]:
        return

    _LOG_STATE["log_index"] += 1
    _LOG_STATE["log_file"] = _build_log_path(_LOG_STATE["logs_dir"], _LOG_STATE["log_date"], _LOG_STATE["log_index"])
    for header_line in _channel_setup_header():
        _write_direct(header_line + "\n")
    for header_line in _rollover_header():
        _write_direct(header_line + "\n")


def _append_raw_line(text):
    encoded_size = len(text.encode("utf-8"))
    _rotate_if_needed(additional_bytes=encoded_size)
    _write_direct(text)


def _append_line(text):
    _append_raw_line(text + "\n")


def _session_header(script_name):
    ts = _now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        "",
        "=" * 88,
        f"SESSION START | time={ts} | script={script_name} | pid={os.getpid()}",
        "=" * 88,
    ]


def _is_channel_setup_line(line):
    stripped = line.strip()
    return stripped.startswith("CHANNEL SETUP")


def _stamp_line_if_needed(line):
    if not line.strip():
        return line
    if _is_channel_setup_line(line):
        return line
    if _TIMESTAMP_PREFIX_RE.match(line):
        return line
    timestamp = _now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] {line}"


def _stamp_message_if_needed(message):
    if "\n" not in message:
        return _stamp_line_if_needed(message)
    return "\n".join(_stamp_line_if_needed(line) for line in message.split("\n"))


def _redirected_print(*args, **kwargs):
    # Respect explicit file routing and temporary stdout redirection used by legacy code paths.
    explicit_file = kwargs.get("file")
    if explicit_file is not None or sys.stdout is not _ORIGINAL_STDOUT:
        _ORIGINAL_PRINT(*args, **kwargs)
        return

    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    message = sep.join(str(arg) for arg in args)
    message = _stamp_message_if_needed(message)
    with _LOCK:
        if not _LOG_STATE["initialized"]:
            init_log_session(script_name=os.path.basename(sys.argv[0]) or "interactive")
        _append_raw_line(message + end)


def init_log_session(script_name="main.py", base_dir=None):
    with _LOCK:
        if _LOG_STATE["initialized"]:
            return _LOG_STATE["log_file"]

        logs_dir, date_str, index, log_file, max_bytes = _daily_log_file(base_dir=base_dir)
        _LOG_STATE["logs_dir"] = logs_dir
        _LOG_STATE["log_date"] = date_str
        _LOG_STATE["log_index"] = index
        _LOG_STATE["log_file"] = log_file
        _LOG_STATE["max_bytes"] = max_bytes
        _LOG_STATE["session_id"] = _now().strftime("%Y%m%d_%H%M%S")
        _LOG_STATE["script_name"] = script_name
        _LOG_STATE["initialized"] = True

        if not os.path.exists(_LOG_STATE["log_file"]) or os.path.getsize(_LOG_STATE["log_file"]) == 0:
            for header_line in _channel_setup_header():
                _append_line(header_line)

        for header_line in _session_header(script_name):
            _append_line(header_line)

        builtins.print = _redirected_print
        return _LOG_STATE["log_file"]


def get_log_file_path():
    return _LOG_STATE["log_file"]


def _format_context(**context):
    parts = []
    for key, value in context.items():
        if value is None:
            continue
        parts.append(f"{key}={value}")
    return " ".join(parts)


def log_checkpoint(component, step, message, **context):
    with _LOCK:
        if not _LOG_STATE["initialized"]:
            init_log_session(script_name=os.path.basename(sys.argv[0]) or "interactive")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context_str = _format_context(**context)
    if context_str:
        print(f"[{timestamp}] [{component}] [{step}] {message} | {context_str}")
    else:
        print(f"[{timestamp}] [{component}] [{step}] {message}")


def log_exception(component, step, exc):
    log_checkpoint(component, step, "Exception", error_type=type(exc).__name__, error=str(exc))