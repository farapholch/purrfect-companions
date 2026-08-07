#!/bin/bash
# Publicerar publish/ till marknadsföringssidan (purrfect.pelleops.se, nginx :8091)
# och till den gamla sökvägen under spelkatten (bakåtkompatibilitet).
set -e
SRC=/opt/purrfect-companions/publish
# Enda destinationen sedan 2026-08-07 — den gamla sökvägen under spelkatten är borttagen.
for D in /var/www/purrfect; do
  mkdir -p "$D"
  cp "$SRC"/*.png "$SRC"/*.md "$SRC"/*.html "$SRC"/*.txt "$D/" 2>/dev/null || true
  cp "$SRC"/*.mcaddon "$D/" 2>/dev/null || true
  chmod 644 "$D"/* 2>/dev/null || true
done
echo "publicerat till /var/www/purrfect (https://purrfect.pelleops.se)"
