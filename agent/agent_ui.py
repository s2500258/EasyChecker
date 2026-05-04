from threading import Event, Thread
import tkinter as tk
from tkinter import ttk
from typing import Optional

from config import get_settings
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
        self.worker_thread = Thread(
            target=run_agent_loop,
            kwargs={
                "state": self.state,
                "stop_event": self.stop_event,
                "log": self._log_status,
            },
            daemon=True,
        )
        self.root = tk.Tk()
        self.root.title("EasyChecker Agent")
        self.root.geometry("560x420")
        self.root.minsize(520, 390)
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        self.status_text = tk.StringVar(value="Starting")
        self.events_sent_text = tk.StringVar(value="0")
        self.started_at_text = tk.StringVar(value=self.state.snapshot().started_at)
        self.last_success_text = tk.StringVar(value="N/A")
        self.last_error_text = tk.StringVar(value="None")
        self.last_event_summary_text = tk.StringVar(value="N/A")
        self.tray_hint_text = tk.StringVar(value="")

        self._tray_icon: Optional["pystray.Icon"] = None
        self._tray_thread: Optional[Thread] = None

        self._build_ui()

    def start(self) -> None:
        self.worker_thread.start()
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

        settings_frame = ttk.LabelFrame(container, text="Active Settings", padding=12)
        settings_frame.pack(fill="x", pady=(14, 0))
        settings_items = [
            ("Backend URL", self.settings.backend_url),
            ("Event source", self.settings.event_source),
            ("Poll interval", f"{self.settings.poll_interval}s"),
            ("Run once", str(self.settings.run_once)),
            ("Host", self.settings.hostname),
            ("Host IP", self.settings.host_ip or "N/A"),
            ("Collect logins", str(self.settings.collect_login_events)),
            ("Collect processes", str(self.settings.collect_process_events)),
            ("Collect services", str(self.settings.collect_service_events)),
            (
                "Process allowlist",
                ", ".join(self.settings.process_name_allowlist) or "all",
            ),
            (
                "Service allowlist",
                ", ".join(self.settings.service_name_allowlist) or "all",
            ),
        ]
        for row_index, (label, value) in enumerate(settings_items):
            self._add_static_row(settings_frame, label, value, row_index)

        controls_frame = ttk.Frame(container, padding=(0, 14, 0, 0))
        controls_frame.pack(fill="x")
        ttk.Button(
            controls_frame,
            text="Minimize to tray",
            command=self.minimize_to_tray,
        ).pack(side="left")
        ttk.Button(
            controls_frame,
            text="Exit agent",
            command=self.exit_agent,
        ).pack(side="left", padx=(10, 0))

        tray_hint = ttk.Label(
            container,
            textvariable=self.tray_hint_text,
            foreground="#68aeb8",
            wraplength=500,
        )
        tray_hint.pack(anchor="w", pady=(10, 0))

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

    def _refresh_ui(self) -> None:
        snapshot = self.state.snapshot()
        self._apply_snapshot(snapshot)
        self.root.after(500, self._refresh_ui)

    def _apply_snapshot(self, snapshot: AgentRuntimeSnapshot) -> None:
        self.started_at_text.set(snapshot.started_at)
        self.status_text.set(snapshot.last_status)
        self.events_sent_text.set(str(snapshot.events_sent))
        self.last_success_text.set(snapshot.last_success_at or "N/A")
        self.last_error_text.set(snapshot.last_error or "None")
        self.last_event_summary_text.set(snapshot.last_event_summary or "N/A")

    def _log_status(self, message: str) -> None:
        # The GUI already shows current values, so keep logging lightweight by
        # feeding only meaningful status text back into the shared state.
        if message.startswith("Agent cycle failed: "):
            self.state.mark_error(message.removeprefix("Agent cycle failed: "))

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
        image = _build_tray_icon_image()
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
        self.stop_event.set()
        if self._tray_icon is not None:
            self._tray_icon.stop()
            self._tray_icon = None
        self.root.destroy()


def _build_tray_icon_image():
    # Generate a tiny in-memory icon so packaging does not depend on an extra
    # .ico asset during the first GUI iteration.
    image = Image.new("RGBA", (64, 64), (15, 29, 35, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((6, 6, 58, 58), radius=12, fill=(18, 78, 88, 255))
    draw.text((18, 19), "EC", fill=(230, 250, 252, 255))
    return image


def main() -> None:
    AgentUI().start()


if __name__ == "__main__":
    main()
