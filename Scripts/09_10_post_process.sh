#!/bin/bash

PRED_DIR=$1
CTMF_DIR=$2
MV_DIR=$3
MQA_DIR=$4
SCRIPT_MV=/home/jarry/Documents/26_SARC/Scripts/09_10_post_process_mv.py
SCRIPT_MQA=/home/jarry/Documents/26_SARC/Scripts/09_10_post_process_mqa.py

mkdir -p "$OUT_DIR"

for pred in "$PRED_DIR"/*.nii.gz
do
    name=$(basename "$pred")

    # extraire le premier nombre du nom
    prefix=${name:0:28}
    # chercher le fichier correspondant dans CTMF
    ctmf=$(ls "$CTMF_DIR"/"$prefix"*.nii.gz 2>/dev/null | head -n 1)
    if [ -f "$ctmf" ]; then

        echo "Match trouvé: $name ↔ $(basename "$ctmf")"

        python "$SCRIPT_MV" \
            --pred "$pred" \
            --ctmf "$ctmf" \
            --out "$MV_DIR"

        python "$SCRIPT_MQA" \
            --pred "$pred" \
            --ctmf "$ctmf" \
            --out "$MQA_DIR"

    else
        echo "Pas de match pour $name"
    fi

done