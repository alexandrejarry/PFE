#!/bin/bash

# ===============================
# Vérification des arguments
# ===============================
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <input_folder> <output_folder>"
    exit 1
fi

INPUT="$1"
OUTPUT="$2"

mkdir -p "$OUTPUT"

# ===============================
# Extraction des fichiers
# ===============================
find "$INPUT" -type f \( -name "*.nii.gz" -o -name "*.nrrd" \) | while read file; do

    filename=$(basename "$file")
    dest="$OUTPUT/$filename"

    # éviter d'écraser si doublon
    if [ -e "$dest" ]; then
        base="${filename%.*}"
        ext="${filename##*.}"
        i=1
        while [ -e "$OUTPUT/${base}_$i.$ext" ]; do
            ((i++))
        done
        dest="$OUTPUT/${base}_$i.$ext"
    fi

    cp "$file" "$dest"
    echo "Copié: $file → $dest"

done

echo "Extraction terminée"
