import os
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt


def view(root_dir, png_root):

    os.makedirs(png_root, exist_ok=True)

    for subdir, dirs, files in os.walk(root_dir):

        nii_files = [f for f in files if f.endswith(".nii.gz")]

        if len(nii_files) < 3:
            continue

        images = []

        for file in sorted(nii_files)[:3]:

            path = os.path.join(subdir, file)

            img = sitk.ReadImage(path)
            img = sitk.DICOMOrient(img, "LAI")

            vol = sitk.GetArrayFromImage(img)  # (z,y,x)

            mid = vol.shape[0] // 2
            slice_img = vol[mid]

            slice_img = slice_img.astype(float)
            slice_img = (slice_img - slice_img.min()) / (slice_img.max() - slice_img.min() + 1e-8)
            rotated = np.rot90(slice_img, 2)

            images.append(rotated)

        # créer la figure
        fig, axes = plt.subplots(1, 3, figsize=(9, 3))

        for i in range(3):
            axes[i].imshow(images[i], cmap="gray")
            axes[i].axis("off")
            axes[i].set_title(f"slice {i+1}")

        plt.tight_layout()

        # nom basé sur le dossier
        folder_name = os.path.basename(subdir)
        out_path = os.path.join(png_root, folder_name + ".png")

        plt.savefig(out_path, bbox_inches="tight")
        plt.close()

        print("saved:", out_path)

    print("Terminé")


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Convertir en PNG")
    parser.add_argument(
        "--input",
        required=True,
        help="Dossier contenant les slices à visualiser"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Dossier où sauvegarder les PNG"
    )

    args = parser.parse_args()

    view(args.input, args.output)