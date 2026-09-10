#!/bin/bash

CT_DIR=$1
SEG_DIR=$2
DATASET_DIR=$3
PRED_DIR=$4
POST_DIR=$5
MV_DIR=$6
OUT_DIR=$7
ALPHA=$8
PY_SCRIPT=$9

for ct in "$CT_DIR"/*.nii.gz; do

    filename=$(basename "$ct")

    # extraire les 28 premiers caractères
    prefix=${filename:0:28}

    echo "Processing $prefix"

    seg_path="None"
    dataset_path="None"

    # segmentation manuelle (dossier)
    seg_match=$(find "$SEG_DIR" -maxdepth 1 -name "${prefix}*" | head -n 1)
    if [ -n "$seg_match" ]; then
        seg_path="$seg_match"
    fi

    # segmentation dataset
    dataset_match=$(find "$DATASET_DIR" -maxdepth 1 -name "${prefix}*.nii.gz" | head -n 1)
    if [ -n "$dataset_match" ]; then
        dataset_path="$dataset_match"
    fi

    pred_path=$(find "$PRED_DIR" -maxdepth 1 -name "${prefix}*.nii.gz" | head -n 1)
    post_path=$(find "$POST_DIR" -maxdepth 1 -name "${prefix}*.nii.gz" | head -n 1)
    mv_path=$(find "$MV_DIR" -maxdepth 1 -name "${prefix}*.nii.gz" | head -n 1)

    python "$PY_SCRIPT" \
        --ct "$ct" \
        --seg "$seg_path" \
        --dataset "$dataset_path" \
        --pred "$pred_path" \
        --post "$post_path" \
        --mv "$mv_path" \
        --output "$OUT_DIR" \
        --alpha "$ALPHA"

done