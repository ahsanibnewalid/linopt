# LinOpt — Linux System Optimizer Suite

<p align="center">
  <img src="assets/linopt-icon.svg" alt="LinOpt app icon" width="180">
</p>

<p align="center">
  <strong>A practical GTK desktop utility for Linux system maintenance and CPU power management.</strong>
</p>

LinOpt is a Python 3 and GTK 3 application designed for Debian and Ubuntu-based Linux systems. It brings common maintenance actions and power-management controls together in one desktop interface, with optional weekly automation using systemd.

## What it does

- **APT maintenance:** remove unused packages and clean the local package cache.
- **System journal cleanup:** vacuum systemd journal logs to a configurable target currently set to 100 MB.
- **CPU governor controls:** select a supported CPU scaling governor through `cpupower`.
- **auto-cpufreq integration:** optionally install, remove, and inspect auto-cpufreq, where Snap support is available.
- **Configuration editor:** view and save `/etc/auto-cpufreq.conf`.
- **Weekly automation:** install or disable a systemd timer for routine package and journal maintenance.
- **Custom branding:** a matching LinOpt SVG icon is included in the repository.

## Requirements

- Debian/Ubuntu-based Linux with systemd
- Python 3
- GTK 3 PyGObject bindings: `python3-gi` and `gir1.2-gtk-3.0`
- PolicyKit / `pkexec` for graphical administrator authentication
- Optional: `linux-cpupower` and `snapd`

## Run from source

Install the main dependencies:

```bash
sudo apt update
sudo apt install python3 python3-gi gir1.2-gtk-3.0 policykit-1 linux-cpupower
```

Then launch from the repository directory:

```bash
pkexec python3 "$PWD/linopt.py"
```

LinOpt requires administrator privileges for system-level operations. Only run it if you trust the source code.

## Build and install the Debian package

From the repository root:

```bash
chmod +x packaging/build-deb.sh
./packaging/build-deb.sh
sudo apt install ./dist/linopt_1.2.0_all.deb
```

The build script creates a local `.deb` package under `dist/`; it does not publish a release automatically.

## Background automation and safety

When enabled, the weekly systemd task runs:

- `apt-get autoclean -y` (cleans downloaded package files; it does not uninstall packages)
- `journalctl --vacuum-size=100M` (permanently removes older journal entries as needed)

The timer runs as root. Journal vacuuming permanently removes older logs. The potentially disruptive `apt-get autoremove` action is available only as a manually confirmed GUI operation, not in unattended maintenance.

Check the timer:

```bash
systemctl status linopt-auto.timer
systemctl list-timers linopt-auto.timer
```

Disable it:

```bash
sudo systemctl disable --now linopt-auto.timer
```

## Project structure

- `linopt.py` — main GTK 3 application
- `assets/linopt-icon.svg` — custom LinOpt icon
- `packaging/debian/control` — Debian package metadata
- `packaging/linopt.desktop` — desktop launcher
- `packaging/build-deb.sh` — local Debian package build script
- `tests/test_linopt.py` — safety regression tests
- `.github/workflows/ci.yml` — syntax checks, regression tests, and Debian package build in GitHub Actions
- `docs/MASTER_PROMPT.md` — reusable prompt for future feature development

## Security and limitations

- Commands are executed using argument lists rather than `shell=True`.
- Available CPU governors depend on the CPU, kernel driver, and distribution.
- auto-cpufreq installation requires Snap support and may not work on every system.
- Test system-level maintenance in a virtual machine before relying on it on an important computer.

## Status

LinOpt is still an early-stage desktop utility. GitHub Actions checks Python syntax, safety regressions, packaging-script syntax, and builds/inspects the Debian package. CI does not validate GUI behavior, administrator authentication, CPU governor support, or systemd behavior on a real desktop. Do not treat LinOpt as production-ready until those manual integration checks pass on supported Debian/Ubuntu releases.
