import os
import pandas as pd
import numpy as np
import SimpleITK as sitk

def extract_slices(nii_folder, csv_path, output_root, labels=[5,6,7,8]):

    os.makedirs(output_root, exist_ok=True)
    df = pd.read_csv(csv_path)

    nii_index = {}
    for f in os.listdir(nii_folder):
        if f.endswith(".nii") or f.endswith(".nii.gz"):
            base = f.replace(".nii.gz","").replace(".nii","")
            nii_index[base] = os.path.join(nii_folder,f)

    for _, row in df.iterrows():

        name = row["nom fichier 3D Slicer"]
        if not isinstance(name, str):
            continue

        base_name = name.replace(".nrrd","").replace(".nnrd","")

        if row["observations (exploitable/nom exploitable (OK/KO))"] != "exploitable":
            continue

        if base_name not in nii_index:
            print("Introuvable:", name)
            continue

        path = nii_index[base_name]
        print("Processing:", path)
        img = sitk.ReadImage(path)
        img = sitk.DICOMOrient(img, "LAI")
        vol = sitk.GetArrayFromImage(img)

        slice_scores = []
        for i in range(vol.shape[0]):
            mask = np.isin(vol[i], labels)
            n_pixels = np.sum(mask)
            if n_pixels > 0:
                slice_scores.append((i, n_pixels))

        if len(slice_scores) == 0:
            print("Aucun label trouvé")
            continue

        slice_scores = sorted(slice_scores, key=lambda x: x[1], reverse=True)
        best_slices = sorted([s[0] for s in slice_scores[:3]])
        out_dir = os.path.join(output_root, base_name)
        os.makedirs(out_dir, exist_ok=True)

        for s in best_slices:
            slice_data = vol[s]
            slice_data = slice_data[np.newaxis,:,:]
            slice_img = sitk.GetImageFromArray(slice_data)
            slice_img.SetSpacing(img.GetSpacing())
            slice_img.SetOrigin(img.GetOrigin())
            slice_img.SetDirection(img.GetDirection())
            out_path = os.path.join(out_dir, f"slice_{s}.nii.gz")
            sitk.WriteImage(slice_img, out_path)
            print("Saved:", out_path)

    print("Extraction terminée")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    extract_slices(args.input, args.csv, args.output)
