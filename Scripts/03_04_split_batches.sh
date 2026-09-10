#!/bin/bash

if [ "$#" -ne 2 ]; then
	echo "Usage: $0 <ct_root> <batch_root>"
	exit 1
fi

CT_ROOT=$1
BATCH_ROOT=$2

mkdir -p "$BATCH_ROOT"

# Nombre d'études total
TOTAL=$(ls -1d $CT_ROOT/* | wc -l)
BATCH_SIZE=$(( (TOTAL + 3) / 4 ))   # arrondi supérieur

echo "Total études: $TOTAL, batch size: $BATCH_SIZE"

i=0
batch=1

for STUDY in "$CT_ROOT"/*; do
    BATCH_DIR="$BATCH_ROOT/batch_$batch"
    mkdir -p "$BATCH_DIR"

    # Copier le dossier de l'étude
    cp -r "$STUDY" "$BATCH_DIR/"

    i=$((i+1))
    if [ $i -ge $BATCH_SIZE ]; then
        i=0
        batch=$((batch+1))
    fi
done
