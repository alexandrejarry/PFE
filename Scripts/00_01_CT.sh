#!/bin/bash

input_dir=$1
output_dir=$2

mkdir -p "$output_dir"

for f in "$input_dir"/*.nii.gz
do
    base=$(basename "$f" .nii.gz)
    cp "$f" "$output_dir/${base}_0000.nii.gz"
done

echo "Terminé."
