import os
import pandas as pd
import numpy as np
import SimpleITK as sitk

def extract_slices_from_csv_sitk(nii_folder, csv_path, output_root):
    """
    Extrait des slices de volumes CT listés dans un CSV et sauvegarde chaque slice en .nii.gz
    Args:
        nii_folder (str): dossier contenant les volumes .nii/.nii.gz
        csv_path (str): chemin vers le CSV contenant les colonnes :
                        "nom fichier 3D Slicer", "observations (exploitable/nom exploitable (OK/KO))",
                        "L3h (num de coupe)", "L3r (num de coupe)", "L3b (num de coupe)"
        output_root (str): dossier où enregistrer les slices extraites
    """
    os.makedirs(output_root, exist_ok=True)

    df = pd.read_csv(csv_path)

    # indexer tous les fichiers .nii/.nii.gz
    paths = [f for f in sorted(os.listdir(nii_folder)) if f.endswith(".nii") or f.endswith(".nii.gz")]

    for _, row in df.iterrows():
        name = row.get("nom fichier 3D Slicer")
        if not isinstance(name, str):
            continue

        prefix_csv = name[:28]

        # chercher le fichier correspondant
        matched_file = None
        for p in paths:
            if p[:28] == prefix_csv:
                matched_file = p
                break

        if matched_file is None:
            print("Aucun CT trouvé pour :", name)
            continue

        if row.get("observations (exploitable/nom exploitable (OK/KO))") != "exploitable":
            continue

        path = os.path.join(nii_folder, matched_file)
        print("processing", path)

        slices = [
            int(row["L3h (num de coupe)"]),
            int(row["L3r (num de coupe)"]),
            int(row["L3b (num de coupe)"])
        ]

        # lecture volume avec SimpleITK
        img = sitk.ReadImage(path)
        img = sitk.DICOMOrient(img, "LAI")
        vol = sitk.GetArrayFromImage(img)  # shape: (slices, height, width)

        new_name = matched_file.replace(".nii","").replace(".gz","")
        out_dir = os.path.join(output_root, new_name)
        os.makedirs(out_dir, exist_ok=True)

        start = max(0, min(slices) - 5)
        end   = min(vol.shape[0]-1, max(slices) + 5)

        print(new_name, "→ slices", start, "à", end)

        for s in range(start, end + 1):
            slice_data = vol[s, :, :]
            slice_data = slice_data[np.newaxis, :, :]  # ajouter dimension z=1

            slice_img = sitk.GetImageFromArray(slice_data)
            # copier métadonnées spatiales
            slice_img.SetSpacing(img.GetSpacing())
            slice_img.SetOrigin(img.GetOrigin())
            slice_img.SetDirection(img.GetDirection())

            out_path = os.path.join(out_dir, f"slice_{s}.nii.gz")
            sitk.WriteImage(slice_img, out_path)

        print("Extraction terminée pour", new_name)

    print("Toutes les slices ont été extraites")


# ============================================
# Permet d’appeler depuis la ligne de commande
# ============================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extraire slices de volumes CT à partir d’un CSV")
    parser.add_argument("--input", required=True, help="Dossier contenant les fichiers .nii/.nii.gz")
    parser.add_argument("--csv", required=True, help="CSV avec les informations sur les volumes et slices")
    parser.add_argument("--output", required=True, help="Dossier de sortie pour les slices")

    args = parser.parse_args()
    extract_slices_from_csv_sitk(args.input, args.csv, args.output)
