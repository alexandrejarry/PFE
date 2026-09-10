#!/bin/bash

# ===============================
# Vérification des arguments
# ===============================

if [ "$#" -ne 3 ]; then
    echo "Usage:"
    echo "./run_convert_nnunet.sh <CT_ROOT> <SEG_ROOT> <OUTPUT_DATASET>"
    exit 1
fi

CT_ROOT="$1"
SEG_ROOT="$2"
OUTPUT_ROOT="$3"

PYTHON_SCRIPT="07_08_dataset.py"   # chemin vers ton script python

echo "===================================="
echo "Conversion dataset vers nnU-Net"
echo "CT folder  : $CT_ROOT"
echo "SEG folder : $SEG_ROOT"
echo "Output     : $OUTPUT_ROOT"
echo "===================================="

python "$PYTHON_SCRIPT" \
    --ct "$CT_ROOT" \
    --seg "$SEG_ROOT" \
    --out "$OUTPUT_ROOT"

echo "Conversion terminée."
