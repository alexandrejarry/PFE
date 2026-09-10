import os
import nibabel as nib
import numpy as np
from scipy import ndimage
from skimage.measure import label
import argparse


def clean_segmentation(input_path, output_root, closing_radius=2):

    # nom de l'étude = dossier contenant le volume/segmentation
    study_name = os.path.basename(os.path.dirname(input_path))

    # dossier de sortie
    output_dir = os.path.join(output_root, study_name)
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "cleaned_segmentation.nii.gz")

    # chargement segmentation
    img = nib.load(input_path)
    seg = np.asanyarray(img.dataobj)
    affine = img.affine

    labels = np.unique(seg)
    labels = labels[labels != 0]

    print("Etude :", study_name)
    print("Labels trouvés :", labels)

    clean = np.zeros_like(seg, dtype=np.uint8)

    for L in labels:

        print("Traitement label :", L)
    
        mask = seg == L
        
        # -------------------------
        # 1. supprimer petits composants
        # -------------------------
        
        cc = label(mask)
        
        if cc.max() == 0:
            continue
        
        sizes = ndimage.sum(mask, cc, range(1, cc.max()+1))
        
        min_size = 100  # à ajuster
        
        keep_components = [
            i+1 for i, size in enumerate(sizes) if size >= min_size
        ]
        
        new_mask = np.isin(cc, keep_components)
        
        # -------------------------
        # 2. fermeture morphologique
        # -------------------------
        
        struct = ndimage.generate_binary_structure(3,1)
        
        new_mask = ndimage.binary_closing(
            new_mask,
            structure=ndimage.iterate_structure(struct, closing_radius)
        )
        
        clean[new_mask] = L

    # sauvegarde
    out = nib.Nifti1Image(clean.astype(np.uint8), affine)
    nib.save(out, output_path)

    print("Segmentation nettoyée sauvegardée :", output_path)
    print("Labels finaux :", np.unique(clean))


def main():

    parser = argparse.ArgumentParser(description="Nettoie une segmentation NIfTI")

    parser.add_argument(
        "--input",
        required=True,
        help="Segmentation NIfTI à nettoyer (sera utilisée aussi pour le nom de l'étude)"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Dossier racine de sortie"
    )

    parser.add_argument(
        "--radius",
        type=int,
        default=2,
        help="Rayon fermeture morphologique"
    )

    args = parser.parse_args()

    clean_segmentation(
        input_path=args.input,
        output_root=args.output,
        closing_radius=args.radius
    )


if __name__ == "__main__":
    main()
