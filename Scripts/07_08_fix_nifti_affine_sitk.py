import os
import argparse
import numpy as np
import SimpleITK as sitk


def orthonormalize_direction(direction):

    # direction arrive sous forme de tuple 9 valeurs
    rot = np.array(direction).reshape(3,3)

    # SVD pour orthonormaliser
    u, _, vh = np.linalg.svd(rot)
    rot_fixed = np.dot(u, vh)

    return tuple(rot_fixed.flatten())


def fix_volume(in_path, out_path):

    img = sitk.ReadImage(in_path)

    direction = img.GetDirection()

    direction_fixed = orthonormalize_direction(direction)

    img.SetDirection(direction_fixed)

    sitk.WriteImage(img, out_path)


def fix_folder(input_dir, output_dir):

    os.makedirs(output_dir, exist_ok=True)

    for f in sorted(os.listdir(input_dir)):

        if not f.endswith(".nii.gz"):
            continue

        in_path = os.path.join(input_dir, f)
        out_path = os.path.join(output_dir, f)

        print("Fixing:", f)

        try:
            fix_volume(in_path, out_path)
        except Exception as e:
            print("Erreur avec", f, e)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True, help="Dossier contenant les nii.gz")
    parser.add_argument("--output", required=True, help="Dossier de sortie corrigé")

    args = parser.parse_args()

    fix_folder(args.input, args.output)


if __name__ == "__main__":
    main()