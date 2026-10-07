#!/usr/bin/env bash
# Installe les dépendances et télécharge les voix françaises Piper (hors ligne).
set -euo pipefail
cd "$(dirname "$0")/.."
pip install piper-tts
mkdir -p voix
for v in fr-gilles-low fr-siwis-medium; do
  [ -f "voix/$v.onnx" ] && continue
  curl -sSL "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-$v.tar.gz" | tar xz -C voix
done
echo "OK. ffmpeg (avec libass et rubberband) doit aussi être installé."
