#!/bin/bash

# =====================================
# Script Bash pour nettoyer tous les volumes NIfTI
# =====================================

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <dossier_racine_sous_dossiers> <dossier_sortie>"
    exit 1
fi

ROOT_DIR="$1"
OUTPUT_ROOT="$2"
PYTHON_SCRIPT="/opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/06_07_cleaner.py"  # <-- à modifier

# parcourir tous les sous-dossiers
for STUDY_DIR in "$ROOT_DIR"/*/; do
    # trouver le volume dans le sous-dossier
    VOLUME=$(find "$STUDY_DIR" -maxdepth 1 -type f \( -iname "*.nii" -o -iname "*.nii.gz" \) | head -n 1)

    if [ -z "$VOLUME" ]; then
        echo "Aucun volume NIfTI trouvé dans $STUDY_DIR"
        continue
    fi

    echo "Traitement du volume : $VOLUME"

    python "$PYTHON_SCRIPT" \
        --input "$VOLUME" \
        --output "$OUTPUT_ROOT"

done

echo "Tous les volumes ont été traités."
