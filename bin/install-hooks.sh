#!/usr/bin/env bash
# Instala los hooks del proyecto CAI

set -e

RAIZ="$(git rev-parse --show-toplevel)"
SRC="$RAIZ/bin/hooks"
DST="$RAIZ/.git/hooks"

if [ ! -d "$SRC" ]; then
  echo "ERROR: no existe $SRC"
  exit 1
fi

mkdir -p "$DST"

for hook in "$SRC"/*; do
  [ -f "$hook" ] || continue
  base="$(basename "$hook")"
  cp "$hook" "$DST/$base"
  chmod +x "$DST/$base"
  echo "Instalado: $base"
done

echo ""
echo "Hooks instalados en .git/hooks/"
echo "Ahora los commits que toquen la bóveda exigen REG- en el mensaje."
