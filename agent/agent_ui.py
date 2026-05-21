from datetime import datetime
from pathlib import Path
from threading import Event, Thread
import sys
import tkinter as tk
from tkinter import ttk
from typing import Optional

from config import get_env_file_path, get_settings
from runner import run_agent_loop
from runtime_state import AgentRuntimeSnapshot, AgentRuntimeState

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - optional at runtime on non-Windows dev machines
    pystray = None
    Image = None
    ImageDraw = None


# Simple Windows control window for the agent.
# The worker thread keeps collecting/sending in the background while this UI
# shows operator-facing status such as start time, current settings, and the
# cumulative number of successfully sent events.
class AgentUI:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.state = AgentRuntimeState()
        self.stop_event = Event()
        self.worker_thread: Optional[Thread] = None
        self.root = tk.Tk()
        self.root.title("EasyChecker Agent")
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        self._window_icon_image: Optional[tk.PhotoImage] = None

        self.status_text = tk.StringVar(value="Starting")
        self.events_sent_text = tk.StringVar(value="0")
        self.started_at_text = tk.StringVar(
            value=_format_timestamp_seconds(self.state.snapshot().started_at)
        )
        self.last_success_text = tk.StringVar(value="N/A")
        self.last_error_text = tk.StringVar(value="None")
        self.last_event_summary_text = tk.StringVar(value="N/A")
        self.process_audit_status_text = tk.StringVar(value="Not checked")
        self.tray_hint_text = tk.StringVar(value="")
        self.settings_save_text = tk.StringVar(value="")

        self.backend_url_edit = tk.StringVar(value=self.settings.backend_url)
        self.poll_interval_edit = tk.StringVar(value=str(self.settings.poll_interval))
        self.collect_logins_edit = tk.BooleanVar(value=self.settings.collect_login_events)
        self.collect_processes_edit = tk.BooleanVar(
            value=self.settings.collect_process_events
        )
        self.collect_services_edit = tk.BooleanVar(
            value=self.settings.collect_service_events
        )
        self.auto_enable_process_audit_edit = tk.BooleanVar(
            value=self.settings.auto_enable_process_audit
        )
        self.run_once_text = tk.StringVar(value=str(self.settings.run_once))
        self.host_ip_text = tk.StringVar(value=self.settings.host_ip or "N/A")
        self.process_allowlist_text = tk.StringVar(
            value=", ".join(self.settings.process_name_allowlist) or "all"
        )
        self.service_allowlist_text = tk.StringVar(
            value=", ".join(self.settings.service_name_allowlist) or "all"
        )

        self._tray_icon: Optional["pystray.Icon"] = None
        self._tray_thread: Optional[Thread] = None

        self._build_ui()
        self._apply_window_icon()
        self._lock_window_size()

    def start(self) -> None:
        self._start_worker()
        self._refresh_ui()
        self.root.mainloop()

    def _build_ui(self) -> None:
        self.root.configure(bg="#0f1d23")

        container = ttk.Frame(self.root, padding=18)
        container.pack(fill="both", expand=True)

        title = ttk.Label(
            container,
            text="EasyChecker Agent",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            container,
            text="Live Windows agent status and current runtime settings",
        )
        subtitle.pack(anchor="w", pady=(2, 14))

        status_frame = ttk.LabelFrame(container, text="Runtime Status", padding=12)
        status_frame.pack(fill="x")
        self._add_kv_row(status_frame, "Started at", self.started_at_text, 0)
        self._add_kv_row(status_frame, "Current status", self.status_text, 1)
        self._add_kv_row(status_frame, "Events sent", self.events_sent_text, 2)
        self._add_kv_row(status_frame, "Last success", self.last_success_text, 3)
        self._add_kv_row(status_frame, "Last event", self.last_event_summary_text, 4)
        self._add_kv_row(status_frame, "Last error", self.last_error_text, 5)
        self._add_kv_row(status_frame, "Process audit", self.process_audit_status_text, 6)

        settings_frame = ttk.LabelFrame(container, text="Active Settings", padding=12)
        settings_frame.pack(fill="x", pady=(14, 0))
        self._add_entry_row(
            settings_frame,
            "Backend URL",
            self.backend_url_edit,
            0,
            width=42,
        )
        self._add_entry_row(
            settings_frame,
            "Poll interval (s)",
            self.poll_interval_edit,
            1,
            width=8,
        )
        self._add_checkbox_row(
            settings_frame,
            "Collect logins",
            self.collect_logins_edit,
            2,
        )
        self._add_checkbox_row(
            settings_frame,
            "Collect processes",
            self.collect_processes_edit,
            3,
        )
        self._add_checkbox_row(
            settings_frame,
            "Collect services",
            self.collect_services_edit,
            4,
        )
        self._add_checkbox_row(
            settings_frame,
            "Auto-enable 4688 audit",
            self.auto_enable_process_audit_edit,
            5,
        )
        self._add_kv_row(settings_frame, "Run once", self.run_once_text, 6)
        self._add_kv_row(settings_frame, "Host IP", self.host_ip_text, 7)
        self._add_kv_row(
            settings_frame,
            "Process allowlist",
            self.process_allowlist_text,
            8,
        )
        self._add_kv_row(
            settings_frame,
            "Service allowlist",
            self.service_allowlist_text,
            9,
        )

        controls_frame = ttk.Frame(container, padding=(0, 14, 0, 0))
        controls_frame.pack(fill="x")
        ttk.Button(
            controls_frame,
            text="Save settings",
            command=self.save_settings,
        ).pack(side="left")
        ttk.Button(
            controls_frame,
            text="Restart agent",
            command=self.restart_agent,
        ).pack(side="left", padx=(10, 0))
        ttk.Button(
            controls_frame,
            text="Minimize to tray",
            command=self.minimize_to_tray,
        ).pack(side="left", padx=(10, 0))
        ttk.Button(
            controls_frame,
            text="Exit agent",
            command=self.exit_agent,
        ).pack(side="left", padx=(10, 0))

        settings_hint = ttk.Label(
            container,
            textvariable=self.settings_save_text,
            foreground="#68aeb8",
            wraplength=500,
        )
        settings_hint.pack(anchor="w", pady=(10, 0))

        tray_hint = ttk.Label(
            container,
            textvariable=self.tray_hint_text,
            foreground="#68aeb8",
            wraplength=500,
        )
        tray_hint.pack(anchor="w", pady=(6, 0))

    def _lock_window_size(self) -> None:
        # Size the window to the actual content height so it ends right after
        # the control buttons / tray hint, then disable manual resizing.
        self.root.update_idletasks()
        width = max(520, self.root.winfo_reqwidth() - 40)
        height = max(180, self.root.winfo_reqheight() - 40)
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(False, False)

    def _apply_window_icon(self) -> None:
        ico_path = _find_logo_ico_path()
        if ico_path is not None:
            try:
                # Windows title-bar icons are most reliable when applied from
                # a real .ico file via iconbitmap instead of iconphoto.
                self.root.iconbitmap(default=str(ico_path))
                return
            except tk.TclError:
                pass

        png_path = _find_logo_png_path()
        if png_path is None:
            return
        try:
            self._window_icon_image = tk.PhotoImage(file=str(png_path))
            self.root.iconphoto(True, self._window_icon_image)
        except tk.TclError:
            self._window_icon_image = None

    def _add_kv_row(
        self, parent: ttk.LabelFrame, label: str, variable: tk.StringVar, row: int
    ) -> None:
        ttk.Label(parent, text=f"{label}:").grid(
            row=row, column=0, sticky="nw", padx=(0, 14), pady=3
        )
        ttk.Label(parent, textvariable=variable, wraplength=360).grid(
            row=row, column=1, sticky="nw", pady=3
        )

    def _add_static_row(
        self, parent: ttk.LabelFrame, label: str, value: str, row: int
    ) -> None:
        ttk.Label(parent, text=f"{label}:").grid(
            row=row, column=0, sticky="nw", padx=(0, 14), pady=2
        )
        ttk.Label(parent, text=value, wraplength=360).grid(
            row=row, column=1, sticky="nw", pady=2
        )

    def _add_entry_row(
        self,
        parent: ttk.LabelFrame,
        label: str,
        variable: tk.StringVar,
        row: int,
        *,
        width: int,
    ) -> None:
        ttk.Label(parent, text=f"{label}:").grid(
            row=row, column=0, sticky="nw", padx=(0, 14), pady=2
        )
        ttk.Entry(parent, textvariable=variable, width=width).grid(
            row=row, column=1, sticky="nw", pady=2
        )

    def _add_checkbox_row(
        self,
        parent: ttk.LabelFrame,
        label: str,
        variable: tk.BooleanVar,
        row: int,
    ) -> None:
        ttk.Label(parent, text=f"{label}:").grid(
            row=row, column=0, sticky="nw", padx=(0, 14), pady=2
        )
        ttk.Checkbutton(parent, variable=variable).grid(
            row=row, column=1, sticky="nw", pady=2
        )

    def _refresh_ui(self) -> None:
        snapshot = self.state.snapshot()
        self._apply_snapshot(snapshot)
        self.root.after(500, self._refresh_ui)

    def _apply_snapshot(self, snapshot: AgentRuntimeSnapshot) -> None:
        self.started_at_text.set(_format_timestamp_seconds(snapshot.started_at))
        self.status_text.set(snapshot.last_status)
        self.events_sent_text.set(str(snapshot.events_sent))
        self.last_success_text.set(
            _format_timestamp_seconds(snapshot.last_success_at)
            if snapshot.last_success_at
            else "N/A"
        )
        self.last_error_text.set(snapshot.last_error or "None")
        self.last_event_summary_text.set(snapshot.last_event_summary or "N/A")
        self.process_audit_status_text.set(snapshot.process_audit_status or "Not checked")

    def _log_status(self, message: str) -> None:
        # The GUI already shows current values, so keep logging lightweight by
        # feeding only meaningful status text back into the shared state.
        if message.startswith("Agent cycle failed: "):
            self.state.mark_error(message.removeprefix("Agent cycle failed: "))

    def _start_worker(self) -> None:
        self.stop_event = Event()
        self.worker_thread = Thread(
            target=run_agent_loop,
            kwargs={
                "state": self.state,
                "stop_event": self.stop_event,
                "log": self._log_status,
            },
            daemon=True,
        )
        self.worker_thread.start()

    def _stop_worker(self) -> None:
        self.stop_event.set()
        if self.worker_thread is not None:
            self.worker_thread.join(timeout=3)
            self.worker_thread = None

    def _reload_settings(self) -> None:
        get_settings.cache_clear()
        self.settings = get_settings()
        self.backend_url_edit.set(self.settings.backend_url)
        self.poll_interval_edit.set(str(self.settings.poll_interval))
        self.collect_logins_edit.set(self.settings.collect_login_events)
        self.collect_processes_edit.set(self.settings.collect_process_events)
        self.collect_services_edit.set(self.settings.collect_service_events)
        self.auto_enable_process_audit_edit.set(
            self.settings.auto_enable_process_audit
        )
        self.run_once_text.set(str(self.settings.run_once))
        self.host_ip_text.set(self.settings.host_ip or "N/A")
        self.process_allowlist_text.set(
            ", ".join(self.settings.process_name_allowlist) or "all"
        )
        self.service_allowlist_text.set(
            ", ".join(self.settings.service_name_allowlist) or "all"
        )

    def save_settings(self) -> None:
        poll_interval_text = self.poll_interval_edit.get().strip()
        if not poll_interval_text.isdigit() or int(poll_interval_text) <= 0:
            self.settings_save_text.set(
                "Poll interval must be a positive whole number. Changes were not saved."
            )
            return

        updates = {
            "BACKEND_URL": self.backend_url_edit.get().strip(),
            "POLL_INTERVAL": poll_interval_text,
            "COLLECT_LOGIN_EVENTS": str(self.collect_logins_edit.get()).lower(),
            "COLLECT_PROCESS_EVENTS": str(self.collect_processes_edit.get()).lower(),
            "COLLECT_SERVICE_EVENTS": str(self.collect_services_edit.get()).lower(),
            "AUTO_ENABLE_PROCESS_AUDIT": str(
                self.auto_enable_process_audit_edit.get()
            ).lower(),
        }
        _save_env_updates(updates)
        self.settings_save_text.set(
            "Settings saved to .env. Restart the agent to apply them to the running worker."
        )

    def restart_agent(self) -> None:
        self.settings_save_text.set("Restarting agent with current .env settings...")
        self._stop_worker()
        self.state = AgentRuntimeState()
        self._reload_settings()
        self._apply_snapshot(self.state.snapshot())
        self._start_worker()
        self.settings_save_text.set("Agent restarted with the latest saved settings.")

    def minimize_to_tray(self) -> None:
        if pystray is None or Image is None or ImageDraw is None:
            self.tray_hint_text.set(
                "Tray support is unavailable until pystray and Pillow are installed."
            )
            self.root.iconify()
            return

        self.root.withdraw()
        self.tray_hint_text.set("Agent hidden to tray. Use the tray menu to reopen it.")
        if self._tray_icon is None:
            self._start_tray_icon()

    def _start_tray_icon(self) -> None:
        image = _load_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("Open", self._on_tray_open),
            pystray.MenuItem("Exit", self._on_tray_exit),
        )
        self._tray_icon = pystray.Icon("easychecker-agent", image, "EasyChecker Agent", menu)
        self._tray_thread = Thread(target=self._tray_icon.run, daemon=True)
        self._tray_thread.start()

    def _on_tray_open(self, icon, item) -> None:  # pragma: no cover - UI callback
        del icon, item
        self.root.after(0, self.restore_from_tray)

    def _on_tray_exit(self, icon, item) -> None:  # pragma: no cover - UI callback
        del icon, item
        self.root.after(0, self.exit_agent)

    def restore_from_tray(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def exit_agent(self) -> None:
        self._stop_worker()
        if self._tray_icon is not None:
            self._tray_icon.stop()
            self._tray_icon = None
        self.root.destroy()


def _load_tray_icon_image():
    # Reuse the same project logo for the tray icon and the window icon so the
    # Windows agent keeps one consistent visual identity.
    logo_path = _find_logo_png_path() or _find_logo_ico_path()
    if logo_path is not None:
        try:
            with Image.open(logo_path) as image:
                tray_image = image.convert("RGBA")
                tray_image.load()
                return tray_image.copy()
        except OSError:
            pass

    image = Image.new("RGBA", (64, 64), (15, 29, 35, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((6, 6, 58, 58), radius=12, fill=(18, 78, 88, 255))
    draw.text((18, 19), "EC", fill=(230, 250, 252, 255))
    return image


def _find_logo_png_path() -> Optional[Path]:
    return _find_asset_path("logo1.png")


def _find_logo_ico_path() -> Optional[Path]:
    return _find_asset_path("logo1.ico")


def _find_asset_path(filename: str) -> Optional[Path]:
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / filename)

    current_dir = Path(__file__).resolve().parent
    candidates.extend(
        [
            current_dir / filename,
            current_dir.parent / filename,
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _format_timestamp_seconds(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _save_env_updates(updates: dict[str, str]) -> None:
    # Update only the targeted keys while preserving the rest of the existing
    # .env file content and comments as much as possible.
    env_path = get_env_file_path()
    existing_lines = []
    if env_path.exists():
        existing_lines = env_path.read_text(encoding="utf-8").splitlines()

    remaining = dict(updates)
    output_lines = []

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            output_lines.append(line)
            continue

        key, _value = line.split("=", 1)
        normalized_key = key.strip()
        if normalized_key in remaining:
            output_lines.append(f"{normalized_key}={remaining.pop(normalized_key)}")
        else:
            output_lines.append(line)

    for key, value in remaining.items():
        output_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")


def main() -> None:
    AgentUI().start()


if __name__ == "__main__":
    main()
