import os
import argparse
from pathlib import Path

import SimpleITK as sitk
import numpy as np


def extract_slices(input_dir, output_root):

    os.makedirs(output_root, exist_ok=True)

    nii_files = [f for f in os.listdir(input_dir) if f.endswith("nii.gz")]

    for file in nii_files:

        volume_path = os.path.join(input_dir, file)

        print("Processing:", volume_path)

        img = sitk.ReadImage(volume_path)
        img = sitk.DICOMOrient(img, "LAI")  # aligner avec l'affichage

        arr = sitk.GetArrayFromImage(img)  # (z, y, x)
        arr= np.rot90(arr, k=2, axes=(1,2))  # aligner avec l'affichage
        # arr = np.flip(arr, axis=(1,2))  # aligner avec l'affichage
        img = sitk.GetImageFromArray(arr)

        size = img.GetSize()  # (x, y, z)
        stats = sitk.StatisticsImageFilter()
        annotated = []

        for z in range(size[2]):

            slice_img = sitk.Extract(img, [size[0], size[1], 0], [0, 0, z])
            stats.Execute(slice_img)

            if stats.GetMaximum() > 0:
                annotated.append(z)

        if len(annotated) < 10:
            print("Not enough annotated slices")
            continue

        first = annotated[5]
        last = annotated[-6]
        middle = annotated[len(annotated)//2]

        selected = [first, middle, last]

        volume_name = Path(file).stem.replace(".nii", "")

        for z in selected:

            # extraire directement la slice
            slice_img = sitk.Extract(img, [size[0], size[1], 0], [0, 0, z])

            # normalisation pour affichage
            slice_img = sitk.RescaleIntensity(slice_img, 0, 255)
            slice_img = sitk.Cast(slice_img, sitk.sitkUInt8)

            out_name = f"{volume_name}_slice{z}.png"
            out_path = os.path.join(output_root, out_name)

            sitk.WriteImage(slice_img, out_path)

            print("Saved:", out_path)


def main():

    parser = argparse.ArgumentParser(description="Extract specific annotated slices")

    parser.add_argument("--input", required=True, help="Directory containing NIfTI volumes")
    parser.add_argument("--output", required=True, help="Output directory for PNG")

    args = parser.parse_args()

    extract_slices(args.input, args.output)


if __name__ == "__main__":
    main()