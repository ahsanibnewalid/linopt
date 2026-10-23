#!/usr/bin/env python3
"""LinOpt — GTK 3 Linux system optimizer for Debian/Ubuntu.

Privileged actions are invoked without a shell. Review each operation before use.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

APP_NAME = "LinOpt System Optimizer Suite"
CONFIG_PATH = Path("/etc/auto-cpufreq.conf")
DEFAULT_CONFIG = """[general]
verbose = false

[battery]
governor = powersave
turbo = never

[charger]
governor = performance
turbo = auto
"""
TIMER_PATH = Path("/etc/systemd/system/linopt-auto.timer")
SERVICE_PATH = Path("/etc/systemd/system/linopt-auto.service")
SCRIPT_PATH = Path("/usr/local/bin/linopt-maintenance")


def run_command(args: list[str], timeout: int = 180) -> tuple[bool, str]:
    """Run a command safely, capturing stdout/stderr and enforcing a timeout."""
    try:
        result = subprocess.run(
            args, check=False, capture_output=True, text=True, timeout=timeout
        )
        output = (result.stdout or "").strip()
        if result.returncode:
            output = (result.stderr or output or f"Exit code {result.returncode}").strip()
            return False, output
        return True, output or "Operation completed successfully."
    except FileNotFoundError:
        return False, f"Required command not found: {args[0]}"
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout} seconds."
    except OSError as exc:
        return False, str(exc)


class LinuxOptimizerApp(Gtk.Window):
    def __init__(self):
        super().__init__(title=APP_NAME)
        self.set_border_width(15)
        self.set_default_size(620, 680)
        self.set_resizable(True)
        # Use a themed icon so the app works both from source and as a .deb.
        # The packaged SVG is installed in the standard hicolor icon theme.
        self.set_icon_name("linopt")

        notebook = Gtk.Notebook()
        self.add(notebook)

        controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        controls.set_border_width(10)
        notebook.append_page(controls, Gtk.Label(label="Optimization Controls"))

        cleanup_frame = Gtk.Frame(label="System Maintenance")
        cleanup = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        cleanup.set_border_width(10)
        cleanup_frame.add(cleanup)
        self.add_button(cleanup, "Clean unused APT packages and package cache",
                        self.on_apt_clean_clicked)
        self.add_button(cleanup, "Limit system journal to 100 MB",
                        self.on_journal_clean_clicked)
        controls.pack_start(cleanup_frame, False, False, 0)

        cpu_frame = Gtk.Frame(label="Manual CPU Governor")
        cpu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        cpu.set_border_width(10)
        cpu_frame.add(cpu)
        grid = Gtk.Grid(column_spacing=10, row_spacing=6)
        grid.attach(Gtk.Label(label="Scaling governor:"), 0, 0, 1, 1)
        self.gov_combo = Gtk.ComboBoxText()
        for governor in ("powersave", "performance", "schedutil", "ondemand", "conservative"):
            self.gov_combo.append_text(governor)
        self.gov_combo.set_active(0)
        grid.attach(self.gov_combo, 1, 0, 1, 1)
        cpu.pack_start(grid, False, False, 0)
        self.add_button(cpu, "Apply CPU governor", self.on_apply_gov_clicked)
        controls.pack_start(cpu_frame, False, False, 0)

        daemon_frame = Gtk.Frame(label="auto-cpufreq")
        daemon = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        daemon.set_border_width(10)
        daemon_frame.add(daemon)
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.add_button(buttons, "Install daemon", self.on_install_autocpu_clicked, expand=True)
        self.add_button(buttons, "Remove daemon", self.on_remove_autocpu_clicked, expand=True)
        daemon.pack_start(buttons, False, False, 0)
        self.add_button(daemon, "Check status / statistics", self.on_status_autocpu_clicked)
        controls.pack_start(daemon_frame, False, False, 0)

        self.status_label = Gtk.Label(label="Ready.")
        self.status_label.set_xalign(0)
        controls.pack_end(self.status_label, False, False, 0)

        config_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        config_tab.set_border_width(10)
        notebook.append_page(config_tab, Gtk.Label(label="auto-cpufreq Profiles"))
        info = Gtk.Label(label=f"Configuration editor: {CONFIG_PATH}")
        info.set_xalign(0)
        config_tab.pack_start(info, False, False, 0)
        scroller = Gtk.ScrolledWindow()
        scroller.set_hexpand(True)
        scroller.set_vexpand(True)
        self.text_view = Gtk.TextView()
        self.text_view.set_monospace(True)
        self.text_buffer = self.text_view.get_buffer()
        scroller.add(self.text_view)
        config_tab.pack_start(scroller, True, True, 0)
        self.add_button(config_tab, "Save configuration and restart daemon",
                        self.on_save_config_clicked)
        
        automation = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        automation.set_border_width(15)
        notebook.append_page(automation, Gtk.Label(label="Background Automation"))
        explanation = Gtk.Label(
            label="Install a weekly systemd timer for package cleanup and journal "
                  "vacuuming. Maintenance runs as root. Review the commands and "
                  "disable the timer whenever you no longer want scheduled cleanup."
        )
        explanation.set_line_wrap(True)
        explanation.set_xalign(0)
        automation.pack_start(explanation, False, False, 0)
        timer_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.add_button(timer_buttons, "Enable weekly timer",
                        self.on_enable_timer_clicked, expand=True)
        self.add_button(timer_buttons, "Disable timer",
                        self.on_disable_timer_clicked, expand=True)
        automation.pack_start(timer_buttons, False, False, 0)
        self.add_button(automation, "Check timer status", self.on_timer_status_clicked)
        self.load_current_config()

    @staticmethod
    def add_button(container, label, callback, expand=False):
        button = Gtk.Button(label=label)
        button.connect("clicked", callback)
        container.pack_start(button, False, bool(expand), 0)
        return button

    def update_status(self, message: str):
        self.status_label.set_text(message)

    def report_command(self, message: str, args: list[str], timeout: int = 180):
        self.update_status(message)
        success, output = run_command(args, timeout)
        self.update_status(("Success: " if success else "Error: ") + output[:500])
        return success, output

    def on_apt_clean_clicked(self, _button):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0, message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Remove unused packages and clean the APT cache?"
        )
        dialog.format_secondary_text(
            "This runs apt-get autoremove and autoclean with automatic confirmation."
        )
        response = dialog.run()
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
            self.update_status("APT cleanup cancelled.")
            return
        success, output = run_command(["apt-get", "autoremove", "-y"], timeout=600)
        if success:
            success, output = run_command(["apt-get", "autoclean", "-y"], timeout=600)
        self.update_status(("Success: " if success else "Error: ") + output[:500])

    def on_journal_clean_clicked(self, _button):
        self.report_command("Vacuuming system journal to 100 MB...",
                            ["journalctl", "--vacuum-size=100M"], timeout=300)

    def on_apply_gov_clicked(self, _button):
        governor = self.gov_combo.get_active_text()
        allowed = {"powersave", "performance", "schedutil", "ondemand", "conservative"}
        if governor not in allowed:
            self.update_status("Choose a valid CPU governor.")
            return
        if shutil.which("cpupower"):
            success, output = run_command(["cpupower", "frequency-set", "-g", governor])
        else:
            success, output = False, "cpupower is not installed; install linux-cpupower first."
        self.update_status(("Success: " if success else "Error: ") + output[:500])

    def on_install_autocpu_clicked(self, _button):
        if not shutil.which("snap"):
            self.update_status("Error: snap is not installed. Install snapd first.")
            return
        success, output = run_command(["snap", "install", "auto-cpufreq"], timeout=900)
        if success:
            success, output = run_command(["auto-cpufreq", "--install"], timeout=900)
        self.update_status(("Success: " if success else "Error: ") + output[:500])
        self.load_current_config()

    def on_remove_autocpu_clicked(self, _button):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0, message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL, text="Remove auto-cpufreq?"
        )
        dialog.format_secondary_text("This removes its system service and Snap package.")
        response = dialog.run()
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
            self.update_status("Removal cancelled.")
            return
        success, output = run_command(["auto-cpufreq", "--remove"], timeout=300)
        if shutil.which("snap"):
            snap_ok, snap_output = run_command(["snap", "remove", "auto-cpufreq"], timeout=600)
            if not snap_ok:
                success, output = False, snap_output
        self.update_status(("Success: " if success else "Error: ") + output[:500])

    def on_status_autocpu_clicked(self, _button):
        success, output = run_command(["auto-cpufreq", "--stats"], timeout=30)
        if success:
            dialog = Gtk.MessageDialog(
                transient_for=self, flags=0, message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK, text="auto-cpufreq telemetry"
            )
            dialog.format_secondary_text(output[:4000])
            dialog.run()
            dialog.destroy()
        else:
            self.update_status("auto-cpufreq is not installed or stats failed: " + output[:300])

    def load_current_config(self):
        try:
            content = CONFIG_PATH.read_text(encoding="utf-8") if CONFIG_PATH.exists() else DEFAULT_CONFIG
        except OSError as exc:
            content = DEFAULT_CONFIG
            self.update_status(f"Could not read config: {exc}")
        self.text_buffer.set_text(content)

    def on_save_config_clicked(self, _button):
        start, end = self.text_buffer.get_bounds()
        content = self.text_buffer.get_text(start, end, True)
        if len(content) > 65536 or "\x00" in content:
            self.update_status("Configuration rejected: invalid or too large.")
            return
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            temp = CONFIG_PATH.with_suffix(".conf.linopt-tmp")
            temp.write_text(content, encoding="utf-8")
            os.chmod(temp, 0o644)
            os.replace(temp, CONFIG_PATH)
            if shutil.which("systemctl"):
                ok, output = run_command(["systemctl", "restart", "auto-cpufreq"], timeout=60)
                if not ok:
                    self.update_status("Saved config; daemon restart reported: " + output[:300])
                    return
            self.update_status("Configuration saved.")
        except OSError as exc:
            self.update_status(f"Could not save configuration: {exc}")

    def on_enable_timer_clicked(self, _button):
        # Scheduled jobs must not remove installed packages unattended.
        # `autoremove` remains available as a manually confirmed GUI action.
        script = """#!/bin/sh
set -eu
/usr/bin/apt-get autoclean -y
/usr/bin/journalctl --vacuum-size=100M
"""
        service = """[Unit]
Description=LinOpt Weekly Maintenance
Documentation=https://github.com/ahsanibnewalid/linopt

[Service]
Type=oneshot
ExecStart=/usr/local/bin/linopt-maintenance
"""
        timer = """[Unit]
Description=Run LinOpt maintenance weekly

[Timer]
OnCalendar=weekly
Persistent=true
RandomizedDelaySec=30m
Unit=linopt-auto.service

[Install]
WantedBy=timers.target
"""
        try:
            SCRIPT_PATH.write_text(script, encoding="utf-8")
            os.chmod(SCRIPT_PATH, 0o755)
            SERVICE_PATH.write_text(service, encoding="utf-8")
            TIMER_PATH.write_text(timer, encoding="utf-8")
        except OSError as exc:
            self.update_status(f"Could not write timer files: {exc}")
            return
        ok, output = run_command(["systemctl", "daemon-reload"], timeout=30)
        if ok:
            ok, output = run_command(["systemctl", "enable", "--now", "linopt-auto.timer"], timeout=60)
        self.update_status(("Success: " if ok else "Error: ") + output[:500])

    def on_disable_timer_clicked(self, _button):
        ok, output = run_command(["systemctl", "disable", "--now", "linopt-auto.timer"], timeout=60)
        if not ok and "not loaded" not in output.lower():
            self.update_status("Could not disable timer: " + output[:300])
            return
        for path in (TIMER_PATH, SERVICE_PATH, SCRIPT_PATH):
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                self.update_status(f"Timer disabled; could not remove {path}: {exc}")
                return
        run_command(["systemctl", "daemon-reload"], timeout=30)
        self.update_status("Weekly automation disabled and unit files removed.")

    def on_timer_status_clicked(self, _button):
        success, output = run_command(["systemctl", "status", "--no-pager", "linopt-auto.timer"], timeout=30)
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK, text="LinOpt timer status"
        )
        dialog.format_secondary_text(output[:4000])
        dialog.run()
        dialog.destroy()


if __name__ == "__main__":
    if os.geteuid() != 0:
        print("LinOpt requires administrator privileges. Launch it through pkexec.", file=sys.stderr)
        sys.exit(1)
    app = LinuxOptimizerApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
