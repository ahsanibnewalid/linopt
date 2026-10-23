#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VERSION=1.2.0
PKGROOT="$ROOT/.build/linopt"
OUT="$ROOT/dist"
rm -rf "$PKGROOT"
mkdir -p "$PKGROOT/DEBIAN" "$PKGROOT/usr/bin" "$PKGROOT/usr/lib/linopt" "$PKGROOT/usr/share/applications" "$PKGROOT/usr/share/icons/hicolor/scalable/apps" "$OUT"
install -m 0644 "$ROOT/packaging/debian/control" "$PKGROOT/DEBIAN/control"
sed "s/^Version: .*/Version: $VERSION/" "$PKGROOT/DEBIAN/control" > "$PKGROOT/DEBIAN/control.tmp"
mv "$PKGROOT/DEBIAN/control.tmp" "$PKGROOT/DEBIAN/control"
install -m 0644 "$ROOT/linopt.py" "$PKGROOT/usr/lib/linopt/linopt.py"
install -m 0644 "$ROOT/packaging/linopt.desktop" "$PKGROOT/usr/share/applications/linopt.desktop"
install -m 0644 "$ROOT/assets/linopt-icon.svg" "$PKGROOT/usr/share/icons/hicolor/scalable/apps/linopt.svg"
cat > "$PKGROOT/usr/bin/linopt" <<'LAUNCHER'
#!/bin/sh
exec /usr/bin/python3 /usr/lib/linopt/linopt.py "$@"
LAUNCHER
chmod 0755 "$PKGROOT/usr/bin/linopt"
dpkg-deb --root-owner-group --build "$PKGROOT" "$OUT/linopt_"$VERSION"_all.deb"
printf 'Package built: %s\n' "$OUT/linopt_"$VERSION"_all.deb"
