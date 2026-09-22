#!/usr/bin/env bash
# Install brain-drain on Raspberry Pi OS (Bookworm or newer). Run as root from the repo:
#   sudo software/deploy/install.sh            # carrier board (real HAL)
#   sudo software/deploy/install.sh --headless # Pi + USB docks, no carrier board (Saturday bench)
set -euo pipefail
MODE="real"; [[ "${1:-}" == "--headless" ]] && MODE="headless"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX=/opt/brain-drain
CONF=/etc/brain-drain/config.json

echo "== apt packages"
apt-get update -qq
apt-get install -y -qq python3-venv python3-dev hdparm nvme-cli sg3-utils smartmontools util-linux libgpiod2 i2c-tools

echo "== venv in $PREFIX"
python3 -m venv "$PREFIX/venv"
EXTRAS="dev"; [[ "$MODE" == "real" ]] && EXTRAS="hw"
"$PREFIX/venv/bin/pip" install -q --upgrade pip
"$PREFIX/venv/bin/pip" install -q "$HERE[$EXTRAS]"

echo "== config"
mkdir -p /etc/brain-drain /var/lib/brain-drain/reports
if [[ ! -f "$CONF" ]]; then
  if [[ "$MODE" == "headless" ]]; then "$PREFIX/venv/bin/braindrain" config-init --headless --config "$CONF"
  else "$PREFIX/venv/bin/braindrain" config-init --config "$CONF"; fi
else
  echo "keeping existing $CONF"
fi

if [[ "$MODE" == "real" ]]; then
  echo "== enable I2C for the OLED"
  CFG=/boot/firmware/config.txt; [[ -f $CFG ]] || CFG=/boot/config.txt
  grep -q '^dtparam=i2c_arm=on' "$CFG" || echo 'dtparam=i2c_arm=on' >> "$CFG"
fi

echo "== systemd"
install -m 644 "$HERE/deploy/brain-drain.service" /etc/systemd/system/brain-drain.service
systemctl daemon-reload
systemctl enable brain-drain.service
echo
echo "Installed. Next:"
echo "  1. plug a dock with a sacrificial drive, then:  $PREFIX/venv/bin/braindrain list --config $CONF"
echo "  2. map it:                                      $PREFIX/venv/bin/braindrain setup-bay 1 /dev/sdX --config $CONF"
echo "  3. bench it:                                    $PREFIX/venv/bin/braindrain bench /dev/sdX --destructive"
echo "  4. start the service:                           systemctl start brain-drain && journalctl -fu brain-drain"
echo "     policy in headless mode comes from headless_dip in $CONF (default 00000000 = AUTO, zeros, full verify)"
