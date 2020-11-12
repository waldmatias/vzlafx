#!/usr/bin/env bash
OUT_DIR="data"
FILENAME=$(date "+%Y-%m-%d.%H%M")

./usd.py > $OUT_DIR/$FILENAME
cat $OUT_DIR/$FILENAME

