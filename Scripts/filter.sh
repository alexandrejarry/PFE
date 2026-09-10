#!/bin/bash

INPUT_DIR=$1
OUTPUT_DIR=$2
SCRIPT=07_08_filter_label.py

# parcourir tous les fichiers nii / nii.gz
find "$INPUT_DIR" -type f \( -name "*.nii" -o -name "*.nii.gz" \) | while read file
do
    # chemin relatif par rapport au dossier d'entrée
    rel_path=${file#$INPUT_DIR/}

    # chemin du fichier de sortie
    out_file="$OUTPUT_DIR/$rel_path"

    # créer le dossier correspondant dans OUTPUT_DIR
    mkdir -p "$(dirname "$out_file")"

    echo "Processing $file → $out_file"

    python3 "$SCRIPT" "$file" "$out_file"

done

echo "Traitement terminé"