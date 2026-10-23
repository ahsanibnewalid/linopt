# LinOpt — Linux System Optimizer

GTK 3 utility for Debian/Ubuntu: APT cleanup, system journal vacuuming, CPU governor controls, optional auto-cpufreq management, configuration editing, and a weekly systemd maintenance timer.

## Requirements
Python 3, PyGObject/GTK 3, PolicyKit/pkexec, and systemd. Optional commands include linux-cpupower and snapd.

## Run from source
Install `python3-gi`, `gir1.2-gtk-3.0`, and `policykit-1`, then launch with `pkexec python3 linopt.py`.

## Build a Debian package
From the repository root run:

```sh
chmod +x packaging/build-deb.sh
./packaging/build-deb.sh
sudo apt install ./dist/linopt_1.2.0_all.deb
```

## Background timer
The optional weekly task runs `apt-get autoremove`, `apt-get autoclean`, and `journalctl --vacuum-size=100M` as root. Review these operations before enabling the timer. Inspect with `systemctl status linopt-auto.timer`; disable with `sudo systemctl disable --now linopt-auto.timer`.

## Repository files
`linopt.py` is the application; `packaging/` contains Debian metadata, launcher, and build script; `assets/linopt-icon.svg` is the custom icon; `docs/MASTER_PROMPT.md` is the future development prompt.

Commands are executed without `shell=True`. Test system-level maintenance in a VM before relying on it.