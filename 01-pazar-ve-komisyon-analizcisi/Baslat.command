#!/bin/bash
# macOS: bu dosyaya çift tıklayın. Program tarayıcınızda açılır.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  python3 arayuz.py
else
  echo ""
  echo "Python bulunamadı."
  echo "Önce https://www.python.org/downloads/ adresinden Python'u kurun,"
  echo "sonra bu dosyaya yeniden çift tıklayın."
  echo ""
  read -n 1 -s -r -p "Kapatmak için bir tuşa basın..."
fi
