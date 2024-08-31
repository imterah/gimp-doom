#!/usr/bin/env bash
if [[ "$1" == "" ]]; then
  echo "Usage: ./install.sh [install_directory]"
  exit 1
fi

rm -rf "$1/gimp-doom"
mkdir "$1/gimp-doom"

cp plugin.py "$1/gimp-doom/gimp-doom.py"
cp -r .venv/lib/python3.*/site-packages "$1/gimp-doom/packages"

if [ -d ".venv/lib64" ]; then
  cp -r .venv/lib64/python3.*/site-packages "$1/gimp-doom/packages64"
fi

if [ -f "doom.wad" ]; then
  cp doom.wad "$1/gimp-doom/"
fi