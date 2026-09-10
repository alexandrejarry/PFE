import os
import nibabel as nib
import numpy as np
import argparse


def get_slice_number(name):
    try:
        return int(name.split("_")[1])
    except:
        return -1


def reconstruct_volume(ct_path, malf_folder, output_root):

    study_name = os.path.basename(malf_folder)

    output_dir = os.path.join(output_root, study_name)
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "reconstructed_labels.nii.gz")

    # =============================
    # CHARGER VOLUME CT
    # =============================

    ct_img = nib.load(ct_path)
    ct_volume = np.asanyarray(ct_img.dataobj)

    ct_shape = ct_volume.shape
    affine = ct_img.affine

    print("CT volume shape:", ct_shape)

    # =============================
    # CREER VOLUME SEGMENTATION
    # =============================

    seg_volume = np.zeros(ct_shape, dtype=np.uint8)

    # =============================
    # INSERER LES LABELS
    # =============================

    for slice_dir in os.listdir(malf_folder):

        slice_number = get_slice_number(slice_dir)
        if slice_number < 0:
            continue

        label_path = os.path.join(malf_folder, slice_dir, "Labels.nii.gz")

        if not os.path.exists(label_path):
            continue

        label_img = nib.load(label_path)
        label_data = np.asanyarray(label_img.dataobj)

        if label_data.ndim == 3:
            label_data = label_data[:, :, 0]

        if label_data.shape != ct_shape[:2]:
            print(f"Shape mismatch pour {slice_dir}")
            continue

        if slice_number >= ct_shape[2]:
            print(f"Slice {slice_number} hors volume")
            continue

        seg_volume[:, :, ct_shape[2] - 1 - slice_number] = label_data
        
    # =============================
    # SAUVEGARDE
    # =============================

    out_img = nib.Nifti1Image(seg_volume.astype(np.uint8), affine)
    nib.save(out_img, output_path)

    print("Volume reconstruit :", output_path)
    print("Labels présents :", np.unique(seg_volume))


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ct",
        required=True,
        help="Chemin vers le volume CT (.nii ou .nii.gz)"
    )

    parser.add_argument(
        "--study",
        required=True,
        help="Dossier contenant slice_xxx/Labels.nii.gz"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Dossier racine de sortie"
    )

    args = parser.parse_args()

    reconstruct_volume(
        ct_path=args.ct,
        malf_folder=args.study,
        output_root=args.output
    )


if __name__ == "__main__":
    main()