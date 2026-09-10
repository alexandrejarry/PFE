#!/bin/bash

# ======================================================
# Script pipeline complet nnU-Net (modifications directes)
# ======================================================

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <CT_ROOT> <SEG_ROOT> <OUTPUT_DATASET>"
    exit 1
fi

CT_ROOT="$1"
SEG_ROOT="$2"
OUTPUT_ROOT="$3"

PYTHON_CONVERT="07_08_dataset.py"       # conversion dataset
PYTHON_FIX_AFFINE="07_08_fix_nifti_affine_sitk.py"
PYTHON_FILTER_LABEL="07_08_filter_label.py"
PYTHON_JSON="07_08_correct_json.py"

echo "===================================="
echo "Conversion dataset vers nnU-Net"
echo "CT folder  : $CT_ROOT"
echo "SEG folder : $SEG_ROOT"
echo "Output     : $OUTPUT_ROOT"
echo "===================================="

# 1️⃣ Conversion dataset vers nnU-Net
python "$PYTHON_CONVERT" \
    --ct "$CT_ROOT" \
    --seg "$SEG_ROOT" \
    --out "$OUTPUT_ROOT"

# 2️⃣ Correction des affines directement dans le dataset
echo "Correction des imagesTr"
python "$PYTHON_FIX_AFFINE" --input "$OUTPUT_ROOT/imagesTr" --output "$OUTPUT_ROOT/imagesTr"

echo "Correction des labelsTr"
python "$PYTHON_FIX_AFFINE" --input "$OUTPUT_ROOT/labelsTr" --output "$OUTPUT_ROOT/labelsTr"

# 3️⃣ Filtrage des labels directement dans les labels existants
find "$OUTPUT_ROOT/labelsTr" -type f -name "*.nii.gz" | while read file
do
    echo "Filtrage $file"
    python "$PYTHON_FILTER_LABEL" "$file" "$file"
done

# 4️⃣ Création du dataset.json directement dans le dossier
python "$PYTHON_JSON"

echo "Pipeline terminé. Dataset prêt dans : $OUTPUT_ROOT"