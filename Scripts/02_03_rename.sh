#!/bin/bash

# ===============================
# Vérification des arguments
# ===============================
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <slice_ct_root> <slice_seg_root> <output_root>"
    exit 1
fi

SLICE_CT_ROOT="$1"
SLICE_SEG_ROOT="$2"
OUTPUT_ROOT="$3"

mkdir -p "$OUTPUT_ROOT"

# ===============================
# Parcourir les dossiers CT
# ===============================
for ct_path in "$SLICE_CT_ROOT"/*; do

    [ -d "$ct_path" ] || continue

    ct_dir=$(basename "$ct_path")
    ct_prefix=${ct_dir:0:28}

    matched_seg=""

    # chercher dossier correspondant
    for seg_path in "$SLICE_SEG_ROOT"/*; do

        [ -d "$seg_path" ] || continue

        seg_dir=$(basename "$seg_path")

        if [[ "$seg_dir" == "$ct_prefix"* ]]; then
            matched_seg="$seg_dir"
            break
        fi
    done

    if [ -z "$matched_seg" ]; then
        echo "Aucun dossier seg trouvé pour $ct_dir"
        continue
    fi

    src_path="$SLICE_SEG_ROOT/$matched_seg"
    dst_path="$OUTPUT_ROOT/$ct_dir"

    cp -r "$src_path" "$dst_path"

    echo "Copié $matched_seg → $dst_path"

done

echo "Renommage terminé."
