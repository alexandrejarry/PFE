import os
import SimpleITK as sitk

def convert_nrrd_to_nii(input_folder, output_folder):
    """
    Parcours tous les fichiers .nrrd dans input_folder et les convertit en .nii.gz
    dans output_folder.
    """
    os.makedirs(output_folder, exist_ok=True)

    for root, dirs, files in os.walk(input_folder):
        for f in files:
            if f.endswith(".nrrd"):
                nrrd_path = os.path.join(root, f)
                # nouveau nom .nii.gz
                base_name = os.path.splitext(f)[0]
                nii_path = os.path.join(output_folder, base_name + ".nii.gz")

                # lecture NRRD
                img = sitk.ReadImage(nrrd_path)
                # écriture NIfTI
                sitk.WriteImage(img, nii_path)

                print(f"{nrrd_path} → {nii_path}")

    print("Conversion terminée.")

# ============================================
# Permet d'appeler la fonction depuis le terminal
# ============================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert NRRD files to NIfTI (.nii.gz)")
    parser.add_argument("--input", required=True, help="Dossier contenant les fichiers .nrrd")
    parser.add_argument("--output", required=True, help="Dossier de sortie pour les fichiers .nii.gz")

    args = parser.parse_args()

    convert_nrrd_to_nii(args.input, args.output)
