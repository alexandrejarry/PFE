#!/bin/bash

# ===============================
# PARAMÈTRES À MODIFIER
# ===============================
SOURCE_DIR="/opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/Total_arranged_L3"  # dossiers patients : s0001, s0002, ...
DEST_DIR="/opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/Dataset001_Pretrain"

# Labels pour dataset.json
declare -A LABELS
LABELS[0]="vertebrae"
LABELS[1]="autochtones"
LABELS[2]="iliopsoas"
LABELS[3]="ribs"

# ===============================
# CRÉATION DE L'ARBORESCENCE
# ===============================
mkdir -p "$DEST_DIR/imagesTr"
mkdir -p "$DEST_DIR/labelsTr"

# ===============================
# COPIE DES FICHIERS
# ===============================
for PATIENT_DIR in "$SOURCE_DIR"/s*; do
    if [ -d "$PATIENT_DIR" ]; then
        PATIENT_ID=$(basename "$PATIENT_DIR")   # ex: s0001
        IMAGE_SRC="$PATIENT_DIR/ct.nii.gz"
        LABEL_SRC="$PATIENT_DIR/fusion.nii.gz"

        # Vérification des fichiers
        if [ ! -f "$IMAGE_SRC" ] || [ ! -f "$LABEL_SRC" ]; then
            echo "Attention : fichiers manquants pour $PATIENT_ID"
            continue
        fi

        # Noms des fichiers dans nnU-Net
        IMAGE_DEST="$DEST_DIR/imagesTr/${PATIENT_ID}_0000.nii.gz"
        LABEL_DEST="$DEST_DIR/labelsTr/${PATIENT_ID}.nii.gz"

        cp "$IMAGE_SRC" "$IMAGE_DEST"
        cp "$LABEL_SRC" "$LABEL_DEST"

        echo "Patient $PATIENT_ID traité."
    fi
done

# ===============================
# GÉNÉRATION DU dataset.json
# ===============================
JSON_FILE="$DEST_DIR/dataset.json"
NUM_TRAIN=$(ls "$DEST_DIR/imagesTr" | wc -l)

echo "{" > "$JSON_FILE"
echo "  \"name\": \"Dataset001_Pretrain\"," >> "$JSON_FILE"
echo "  \"description\": \"Segmentation muscles L3\"," >> "$JSON_FILE"
echo "  \"tensorImageSize\": \"3D\"," >> "$JSON_FILE"
echo "  \"modality\": { \"0\": \"CT\" }," >> "$JSON_FILE"
echo "  \"labels\": {" >> "$JSON_FILE"

# Labels
FIRST=1
for i in "${!LABELS[@]}"; do
    if [ $FIRST -eq 1 ]; then FIRST=0; else echo "," >> "$JSON_FILE"; fi
    echo "    \"$i\": \"${LABELS[$i]}\"" >> "$JSON_FILE"
done
echo "  }," >> "$JSON_FILE"

echo "  \"numTraining\": $NUM_TRAIN," >> "$JSON_FILE"
echo "  \"training\": [" >> "$JSON_FILE"

FIRST_PAT=1
for IMAGE_PATH in "$DEST_DIR/imagesTr"/*.nii.gz; do
    BASE=$(basename "$IMAGE_PATH" "_0000.nii.gz")
    LABEL_PATH="$DEST_DIR/labelsTr/${BASE}.nii.gz"

    if [ $FIRST_PAT -eq 1 ]; then FIRST_PAT=0; else echo "," >> "$JSON_FILE"; fi
    echo "    {\"image\": \"./imagesTr/${BASE}_0000.nii.gz\", \"label\": \"./labelsTr/${BASE}.nii.gz\"}" >> "$JSON_FILE"
done

echo "  ]," >> "$JSON_FILE"
echo "  \"numTest\": 0," >> "$JSON_FILE"
echo "  \"test\": []" >> "$JSON_FILE"
echo "}" >> "$JSON_FILE"

echo "Dataset prêt : structure nnU-Net et dataset.json créés dans $DEST_DIR"
