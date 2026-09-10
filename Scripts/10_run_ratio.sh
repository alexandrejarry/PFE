#!/bin/bash

seg_perso_dir=$1
seg_total_dir=$2
output_dir=$3

python_script="09_statistics.py"

mkdir -p "$output_dir"

for perso_file in "$seg_perso_dir"/*.nii.gz
do

    filename=$(basename "$perso_file")
    total_file="$seg_total_dir/$filename"

    if [ -f "$total_file" ]; then

        echo "Processing $filename"

        python "$python_script" \
            "$perso_file" \
            "$total_file" \
            "$output_dir"

    else

        echo "Warning: $filename not found in total segmentation folder"

    fi

done

echo "Processing finished."
