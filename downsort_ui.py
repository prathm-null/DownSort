import sys
import math
import datetime
import tkinter as tk
from pathlib import Path
from sorter_engine import DownSortEngine
from watcher import DownSortWatcher

STARTUP_DIR = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
STARTUP_SCRIPT = STARTUP_DIR / "DownSort_AutoStart.vbs"


class DownSortHUD:
    def __init__(self, root: tk.Tk, start_minimized: bool = False):
        self.root = root
        self.root.title("DOWNSORT // AUTONOMOUS FILE TELEMETRY")
        self.root.geometry("640x540")
        self.root.configure(bg="#060a12")
        self.root.resizable(False, False)

        icon_file = Path(__file__).with_name("downsort.ico")
        if icon_file.exists():
            self.root.iconbitmap(str(icon_file))

        self.is_paused = False
        self.phase = 0.0

        self.engine = DownSortEngine(log_callback=self.on_engine_log)
        self.watcher = DownSortWatcher(self.engine)

        self._build_ui()
        self._animate_scanner()
        self.watcher.start()

        if start_minimized:
            self.root.iconify()

    def _build_ui(self):
        header_frame = tk.Frame(self.root, bg="#060a12")
        header_frame.pack(fill="x", padx=20, pady=(16, 6))

        tk.Label(
            header_frame,
            text="DOWNSORT  //  MK-I",
            font=("Consolas", 15, "bold"),
            fg="#00f3ff",
            bg="#060a12"
        ).pack(side="left")

        self.status_lbl = tk.Label(
            header_frame,
            text="[ SENSOR: ACTIVE ]",
            font=("Consolas", 10, "bold"),
            fg="#00ff9d",
            bg="#060a12"
        )
        self.status_lbl.pack(side="right")

        target_lbl = tk.Label(
            self.root,
            text=f"TARGET DIRECTORY: {self.engine.downloads_dir}",
            font=("Consolas", 9),
            fg="#568299",
            bg="#060a12",
            anchor="w"
        )
        target_lbl.pack(fill="x", padx=20, pady=(0, 10))

        mid_frame = tk.Frame(self.root, bg="#09101d", highlightbackground="#12304a", highlightthickness=1)
        mid_frame.pack(fill="x", padx=20, pady=(0, 12))

        self.canvas = tk.Canvas(mid_frame, width=130, height=130, bg="#09101d", highlightthickness=0)
        self.canvas.pack(side="left", padx=15, pady=10)

        stats_frame = tk.Frame(mid_frame, bg="#09101d")
        stats_frame.pack(side="left", fill="both", expand=True, padx=10, pady=12)

        self.sorted_lbl = tk.Label(
            stats_frame,
            text="FILES SORTED      : 0",
            font=("Consolas", 11, "bold"),
            fg="#00f3ff",
            bg="#09101d",
            anchor="w"
        )
        self.sorted_lbl.pack(fill="x", pady=4)

        self.staged_lbl = tk.Label(
            stats_frame,
            text="PARTIAL SNAPSHOTS : 0",
            font=("Consolas", 11, "bold"),
            fg="#ffb700",
            bg="#09101d",
            anchor="w"
        )
        self.staged_lbl.pack(fill="x", pady=4)

        self.startup_lbl = tk.Label(
            stats_frame,
            text=f"BOOT AUTO-START   : {'ENABLED' if self._is_startup_enabled() else 'DISABLED'}",
            font=("Consolas", 10),
            fg="#8ab4c9",
            bg="#09101d",
            anchor="w"
        )
        self.startup_lbl.pack(fill="x", pady=4)

        btn_frame = tk.Frame(self.root, bg="#060a12")
        btn_frame.pack(fill="x", padx=20, pady=(0, 12))

        self.pause_btn = tk.Button(
            btn_frame,
            text="PAUSE MONITOR",
            font=("Consolas", 9, "bold"),
            fg="#060a12",
            bg="#00f3ff",
            activebackground="#00c4cf",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.toggle_pause
        )
        self.pause_btn.pack(side="left", padx=(0, 8))

        scan_btn = tk.Button(
            btn_frame,
            text="SCAN NOW",
            font=("Consolas", 9, "bold"),
            fg="#00f3ff",
            bg="#0b172a",
            activebackground="#13294a",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.engine.scan_existing_files
        )
        scan_btn.pack(side="left", padx=(0, 8))

        self.startup_btn = tk.Button(
            btn_frame,
            text="DISABLE STARTUP" if self._is_startup_enabled() else "ENABLE STARTUP",
            font=("Consolas", 9, "bold"),
            fg="#00ff9d",
            bg="#0b172a",
            activebackground="#13294a",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.toggle_startup
        )
        self.startup_btn.pack(side="right")

        log_frame = tk.Frame(self.root, bg="#09101d", highlightbackground="#12304a", highlightthickness=1)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.log_box = tk.Text(
            log_frame,
            bg="#070c16",
            fg="#b8f2e6",
            font=("Consolas", 9),
            bd=0,
            padx=10,
            pady=8,
            wrap="word",
            state="disabled"
        )
        self.log_box.pack(fill="both", expand=True)

        self.log_box.tag_config("TIME", foreground="#4a7c8c")
        self.log_box.tag_config("SORTED", foreground="#00ff9d")
        self.log_box.tag_config("STAGING", foreground="#ffb700")
        self.log_box.tag_config("CLEANUP", foreground="#00f3ff")
        self.log_box.tag_config("ERROR", foreground="#ff3b5c")
        self.log_box.tag_config("SYSTEM", foreground="#8ab4c9")
        self.log_box.tag_config("WATCHER", foreground="#00d4ff")

    def _animate_scanner(self):
        self.canvas.delete("all")
        cx, cy = 65, 65
        color = "#ff3b5c" if self.is_paused else "#00f3ff"
        dim = "#3b121c" if self.is_paused else "#10344f"

        self.canvas.create_oval(10, 10, 120, 120, outline=dim, width=2)
        self.canvas.create_oval(28, 28, 102, 102, outline=dim, width=1)

        if not self.is_paused:
            self.phase = (self.phase + 4) % 360

        self.canvas.create_arc(
            14, 14, 116, 116,
            start=self.phase,
            extent=65,
            style="arc",
            outline=color,
            width=3
        )
        self.canvas.create_arc(
            32, 32, 98, 98,
            start=-self.phase * 1.5,
            extent=90,
            style="arc",
            outline=color,
            width=2
        )

        pulse = 0 if self.is_paused else math.sin(math.radians(self.phase * 2)) * 3
        r = 14 + pulse
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=2, fill="#060a12")

        self.root.after(60, self._animate_scanner)

    def on_engine_log(self, tag: str, message: str):
        def _update():
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_box.config(state="normal")
            self.log_box.insert("end", f"[{ts}] ", "TIME")
            self.log_box.insert("end", f"[{tag}] ", tag if tag in ("SORTED", "STAGING", "CLEANUP", "ERROR", "SYSTEM", "WATCHER") else "SYSTEM")
            self.log_box.insert("end", f"{message}\n")
            self.log_box.see("end")
            self.log_box.config(state="disabled")

            self.sorted_lbl.config(text=f"FILES SORTED      : {self.engine.sorted_count}")
            self.staged_lbl.config(text=f"PARTIAL SNAPSHOTS : {self.engine.staged_count}")

        self.root.after(0, _update)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.watcher.set_paused(self.is_paused)
        if self.is_paused:
            self.status_lbl.config(text="[ SENSOR: PAUSED ]", fg="#ff3b5c")
            self.pause_btn.config(text="RESUME MONITOR", bg="#ff3b5c", fg="#ffffff")
        else:
            self.status_lbl.config(text="[ SENSOR: ACTIVE ]", fg="#00ff9d")
            self.pause_btn.config(text="PAUSE MONITOR", bg="#00f3ff", fg="#060a12")

    def _is_startup_enabled(self) -> bool:
        return STARTUP_SCRIPT.exists()

    def toggle_startup(self):
        if self._is_startup_enabled():
            STARTUP_SCRIPT.unlink()
            self.startup_lbl.config(text="BOOT AUTO-START   : DISABLED")
            self.startup_btn.config(text="ENABLE STARTUP")
            self.on_engine_log("SYSTEM", "Removed DownSort from Windows Startup.")
        else:
            STARTUP_DIR.mkdir(parents=True, exist_ok=True)
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            if not pythonw.exists():
                pythonw = Path(sys.executable)
            script_path = Path(__file__).resolve()
            vbs_content = (
                f'Set WshShell = CreateObject("WScript.Shell")\n'
                f'WshShell.Run """{pythonw}"" ""{script_path}"" --minimized", 0, False\n'
            )
            STARTUP_SCRIPT.write_text(vbs_content, encoding="utf-8")
            self.startup_lbl.config(text="BOOT AUTO-START   : ENABLED")
            self.startup_btn.config(text="DISABLE STARTUP")
            self.on_engine_log("SYSTEM", "Registered DownSort in Windows Startup (silent boot).")

    def on_close(self):
        self.watcher.stop()
        self.root.destroy()


if __name__ == "__main__":
    minimized = "--minimized" in sys.argv
    root = tk.Tk()
    app = DownSortHUD(root, start_minimized=minimized)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()