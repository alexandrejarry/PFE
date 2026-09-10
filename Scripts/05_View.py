import os
import re
import argparse
from pathlib import Path

import SimpleITK as sitk
import numpy as np


def convert_dataset(input_root, output_root, include_parent):

    os.makedirs(output_root, exist_ok=True)

    pattern = re.compile(r"slice_(\d+)")

    for root, dirs, files in os.walk(input_root):

        folder_name = os.path.basename(root)
        match = pattern.match(folder_name)

        if match and "Labels.nii.gz" in files:

            slice_id = match.group(1)
            nii_path = os.path.join(root, "Labels.nii.gz")

            print(f"Processing {nii_path}")

            # lecture image
            img = sitk.ReadImage(nii_path)
            img = sitk.GetArrayFromImage(img)  # (z,y,x)
            rotated = np.rot90(img, 2)
            rotated = sitk.GetImageFromArray(rotated)


            out_img = sitk.RescaleIntensity(rotated, 0, 255)
            out_img = sitk.Cast(out_img, sitk.sitkUInt8)


            # nom fichier sortie
            if include_parent:
                parent = Path(root).parts[-2]
                out_name = f"{parent}_slice_{slice_id}.png"
            else:
                out_name = f"slice_{slice_id}.png"

            out_path = os.path.join(output_root, out_name)

            sitk.WriteImage(out_img, out_path)

            print(f"Saved → {out_path}")


def main():

    parser = argparse.ArgumentParser(
        description="Extract Labels.nii.gz from slice folders and save as PNG."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Root directory containing dataset",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for PNG images",
    )

    parser.add_argument(
        "--include-parent",
        action="store_true",
        help="Include parent folder name in output filename",
    )

    args = parser.parse_args()

    convert_dataset(args.input, args.output, args.include_parent)


if __name__ == "__main__":
    main()