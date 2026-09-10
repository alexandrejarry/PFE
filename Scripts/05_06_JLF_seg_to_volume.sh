#!/bin/bash

# ===============================
# PARAMETRES
# ===============================

CT_FOLDER="$1"        # dossier contenant les volumes CT (.nii.gz)
MALF_ROOT="$2"        # dossier contenant les dossiers d'études MALF
OUTPUT_ROOT="$3"      # dossier de sortie
PY_SCRIPT="$4"        # script python reconstruct_volume.py

# ===============================
# VERIFICATION
# ===============================

if [ -z "$CT_FOLDER" ] || [ -z "$MALF_ROOT" ] || [ -z "$OUTPUT_ROOT" ] || [ -z "$PY_SCRIPT" ]; then
    echo "Usage:"
    echo "./run_reconstruction.sh CT_FOLDER MALF_ROOT OUTPUT_ROOT PY_SCRIPT"
    exit 1
fi

# ===============================
# BOUCLE SUR LES VOLUMES CT
# ===============================

for CT_FILE in "$CT_FOLDER"/*.nii.gz; do

    [ -f "$CT_FILE" ] || continue

    FILE_NAME=$(basename "$CT_FILE")
    STUDY_NAME="${FILE_NAME%.nii.gz}"

    echo ""
    echo "===================================="
    echo "Processing volume: $STUDY_NAME"
    echo "===================================="

    STUDY_DIR="$MALF_ROOT/$STUDY_NAME"

    if [ ! -d "$STUDY_DIR" ]; then
        echo "Aucune étude MALF trouvée pour $STUDY_NAME"
        continue
    fi

    python "$PY_SCRIPT" \
        --ct "$CT_FILE" \
        --study "$STUDY_DIR" \
        --output "$OUTPUT_ROOT"

done

echo ""
echo "Reconstruction terminée."
