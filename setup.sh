#!/usr/bin/env bash
set -euo pipefail

echo "🌌 Trinity Protocol - Setup"
echo "=========================="
echo ""

# Resolve script directory for reliable path handling
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Step 1: Initialize state files (fix 0-byte issue)
echo "Step 1: Initializing state files..."
STATE_DIR="$SCRIPT_DIR/state"
mkdir -p "$STATE_DIR"
STATUS_FILE="$STATE_DIR/status.json"
VERIFY_FILE="$STATE_DIR/verify_report.json"
LOCKS_FILE="$STATE_DIR/locks.json"
if [ ! -s "$STATUS_FILE" ]; then
  cat > "$STATUS_FILE" << 'EOF'
{
  "version": "1.0",
  "initialized_at": null,
  "last_updated": null,
  "system": {"status": "idle", "active_capsules": 0, "locked_files": []},
  "current_session": null
}
EOF
  echo "✅ Wrote $STATUS_FILE"
else
  echo "✅ $STATUS_FILE exists"
fi
if [ ! -s "$VERIFY_FILE" ]; then
  echo '{"version":"1.0","result":"pending","gates":{}}' > "$VERIFY_FILE"
  echo "✅ Wrote $VERIFY_FILE"
fi
if [ ! -s "$LOCKS_FILE" ]; then
  echo '{"locks":[]}' > "$LOCKS_FILE"
  echo "✅ Wrote $LOCKS_FILE"
fi
echo ""

# Step 2: Create virtual environment
echo "Step 2: Creating virtual environment..."
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    python3 -m venv "$SCRIPT_DIR/.venv"
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Step 3: Install dependencies
echo ""
echo "Step 3: Installing dependencies..."
source "$SCRIPT_DIR/.venv/bin/activate"
pip install --upgrade pip -q
pip install -r "$SCRIPT_DIR/requirements.txt" -q
echo "✅ Dependencies installed"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. source $SCRIPT_DIR/.venv/bin/activate"
echo "  2. cd $SCRIPT_DIR && python3 -m cli.main session new \"Your Task\""
echo ""
