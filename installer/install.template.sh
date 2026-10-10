#!/usr/bin/env bash
# Workshop: a self-contained installer for macOS and Linux.
set -euo pipefail
YES=0
CHECK=0
for argument in "$@"; do
    case "$argument" in
        --yes) YES=1 ;;
        --check) CHECK=1 ;;
        --help|-h)
            printf 'Workshop\n\nRun: bash install.sh\nOptions: --yes (no prompt), --check (verify package only)\n'
            exit 0 ;;
        *) printf 'Unknown option: %s\n' "$argument" >&2; exit 2 ;;
    esac
done
case "$(uname -s)" in
    Darwin) DEFAULT_BASE="$HOME/Library/Application Support/Workshop" ;;
    Linux) DEFAULT_BASE="${XDG_DATA_HOME:-$HOME/.local/share}/workshop" ;;
    *) printf 'This installer supports macOS and Linux.\n' >&2; exit 1 ;;
esac
BASE="${WORKSHOP_HOME:-$DEFAULT_BASE}"
CONFIG="${WORKSHOP_LMSTUDIO_CONFIG:-$HOME/.lmstudio/mcp.json}"
WORKSPACE="${WORKSHOP_WORKSPACE:-$HOME/Documents/Workshop}"
TEMPORARY="$(mktemp -d "${TMPDIR:-/tmp}/workshop.XXXXXX")"
LOCKED=0
cleanup() {
    rm -rf "$TEMPORARY"
    if [ "$LOCKED" = 1 ]; then
        rm -f "$BASE/install.lock/pid"
        rmdir "$BASE/install.lock" 2>/dev/null || true
    fi
}
trap cleanup EXIT
ARCHIVE="$TEMPORARY/package.tar.gz"
if base64 --decode </dev/null >/dev/null 2>&1; then
    DECODE_FLAG=--decode
else
    DECODE_FLAG=-D
fi
base64 "$DECODE_FLAG" > "$ARCHIVE" <<'WORKSHOP_PAYLOAD'
@@PAYLOAD@@
WORKSHOP_PAYLOAD
if command -v sha256sum >/dev/null 2>&1; then
    ACTUAL="$(sha256sum "$ARCHIVE" | cut -d ' ' -f 1)"
else
    ACTUAL="$(shasum -a 256 "$ARCHIVE" | cut -d ' ' -f 1)"
fi
if [ "$ACTUAL" != "@@SHA256@@" ]; then
    printf 'The installer package is damaged. Download it again.\n' >&2
    exit 1
fi
tar -xzf "$ARCHIVE" -C "$TEMPORARY"
if [ ! -f "$TEMPORARY/workshop/installer/install.py" ]; then
    printf 'The installer package is incomplete.\n' >&2; exit 1
fi
if [ "$CHECK" = 1 ]; then
    printf 'Workshop package verified: eight integrations and Bionic workflows.\n'
    exit 0
fi
printf '\nWorkshop\n\nThis installs eight LM Studio integrations and one Bionic skill.\nExisting LM Studio settings are backed up.\nPython and JavaScript tools run with your user permissions.\nClose LM Studio before continuing.\n\n'
if [ "$YES" = 0 ]; then
    if [ ! -r /dev/tty ]; then
        printf 'Run with --yes for noninteractive installation.\n' >&2; exit 1
    fi
    printf 'Install? [Y/n] ' > /dev/tty
    read -r ANSWER < /dev/tty
    case "$ANSWER" in n|N|no|NO) printf 'Cancelled.\n'; exit 0 ;; esac
fi
mkdir -p "$BASE"
if ! mkdir "$BASE/install.lock" 2>/dev/null; then
    PID="$(cat "$BASE/install.lock/pid" 2>/dev/null || true)"
    if [[ "$PID" =~ ^[0-9]+$ ]] && ! kill -0 "$PID" 2>/dev/null; then
        rm -f "$BASE/install.lock/pid"
        rmdir "$BASE/install.lock"
        mkdir "$BASE/install.lock"
    else
        printf 'Another installation is running. Let it finish first.\n' >&2; exit 1
    fi
fi
LOCKED=1
printf '%s\n' "$$" > "$BASE/install.lock/pid"
RUNTIME="$BASE/runtime"
LOG="$BASE/setup.log"
mkdir -p "$RUNTIME/bin" "$WORKSPACE"
: > "$LOG"
chmod 600 "$LOG"
export UV_CACHE_DIR="$RUNTIME/cache"
export UV_PYTHON_INSTALL_DIR="$RUNTIME/python"
if [ ! -x "$RUNTIME/bin/uv" ]; then
    printf 'Getting the installer tools...\n'
    curl --proto '=https' --tlsv1.2 --fail --location --retry 3 --silent --show-error --output "$TEMPORARY/uv-install.sh" https://astral.sh/uv/install.sh
    if ! UV_UNMANAGED_INSTALL="$RUNTIME/bin" sh "$TEMPORARY/uv-install.sh" >> "$LOG" 2>&1; then
        printf 'Download failed. Details: %s\n' "$LOG" >&2; exit 1
    fi
fi
RELEASE="$BASE/releases/0.3.1-$(date +%s)-$$"
mkdir -p "$RELEASE"
cp -R "$TEMPORARY/workshop/." "$RELEASE/"
if ! "$RUNTIME/bin/uv" run --no-project --managed-python --python 3.12 "$RELEASE/installer/install.py" --release "$RELEASE" --runtime "$RUNTIME" --workspace "$WORKSPACE" --config "$CONFIG" --log "$LOG"; then
    printf '\nSetup failed. Details: %s\n' "$LOG" >&2; exit 1
fi
printf '\nNo compilation or manual configuration was needed.\n'
