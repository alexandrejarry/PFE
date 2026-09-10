import os
import argparse
from pathlib import Path

import SimpleITK as sitk
import numpy as np


def extract_slices(input_root, output_root):

    os.makedirs(output_root, exist_ok=True)

    for root, dirs, files in os.walk(input_root):

        nii_files = [f for f in files if f.endswith(".nii.gz")]

        if len(nii_files) == 0:
            continue

        volume_path = os.path.join(root, nii_files[0])

        print("Processing:", volume_path)

        img = sitk.ReadImage(volume_path)
        img = sitk.DICOMOrient(img, "LAI")

        arr = sitk.GetArrayFromImage(img)  # (z,y,x)

        # détecter slices annotées
        annotated = [i for i in range(arr.shape[0]) if np.any(arr[i] != 0)]

        if len(annotated) < 10:
            print("Not enough annotated slices")
            continue

        first = annotated[5]          # 5e depuis le début
        last = annotated[-6]          # 5e depuis la fin
        middle = annotated[len(annotated)//2]

        selected = [first, middle, last]

        volume_name = Path(root).name

        for idx, z in enumerate(selected):

            slice_arr = arr[z]
            slice_arr = np.rot90(slice_arr, 2)

            slice_img = sitk.GetImageFromArray(slice_arr)

            slice_img = sitk.RescaleIntensity(slice_img, 0, 255)
            slice_img = sitk.Cast(slice_img, sitk.sitkUInt8)

            out_name = f"{volume_name}_slice{z}.png"
            out_path = os.path.join(output_root, out_name)

            sitk.WriteImage(slice_img, out_path)

            print("Saved:", out_path)


def main():

    parser = argparse.ArgumentParser(description="Extract specific annotated slices")

    parser.add_argument("--input", required=True, help="Root directory containing volumes")
    parser.add_argument("--output", required=True, help="Output directory for PNG")

    args = parser.parse_args()

    extract_slices(args.input, args.output)


if __name__ == "__main__":
    main()