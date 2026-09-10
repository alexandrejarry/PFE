#!/bin/bash

# ===============================
# Vérification des arguments
# ===============================
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <ct_root> <seg_root> <output_csv_dir>"
    exit 1
fi

CT_ROOT=$1
SEG_ROOT=$2
CSV_ROOT=$3

mkdir -p "$CSV_ROOT"

# ===============================
# Boucle sur les 4 batches
# ===============================
for i in 1 2 3 4
do
    CT_BATCH="$CT_ROOT/batch_$i"
    SEG_BATCH="$SEG_ROOT/batch_$i"
    OUT_CSV="$CSV_ROOT/atlas_pairs_batch_$i.csv"

    echo "Processing batch $i"

    python 04_create_csv.py \
        --ct_root "$CT_BATCH" \
        --seg_root "$SEG_BATCH" \
        --output_csv "$OUT_CSV"

done

echo "Tous les batches ont été traités."
