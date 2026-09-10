import os
import csv
import argparse


def create_atlas_csv(slice_ct_root, slice_seg_root, output_csv):
    """
    Crée un CSV associant les slices CT et segmentation pour chaque étude.
    Chaque étude doit contenir exactement 3 slices segmentées.
    """

    rows = []

    for study in os.listdir(slice_seg_root):

        seg_study_path = os.path.join(slice_seg_root, study)
        ct_study_path = os.path.join(slice_ct_root, study)

        if not os.path.isdir(seg_study_path) or not os.path.isdir(ct_study_path):
            continue

        # récupérer les slices segmentées
        seg_slices = [
            f for f in os.listdir(seg_study_path)
            if f.endswith(".nii") or f.endswith(".nii.gz")
        ]

        seg_slices = sorted(seg_slices)

        if len(seg_slices) != 3:
            print(f"{study} ignoré : pas exactement 3 slices seg")
            continue

        ct_paths = []
        seg_paths = []

        for s in seg_slices:

            seg_file = os.path.join(seg_study_path, s)
            ct_file = os.path.join(ct_study_path, s)

            if not os.path.exists(ct_file):
                print(f"CT manquant pour {study} -> {s}")
                continue

            seg_paths.append(os.path.abspath(seg_file))
            ct_paths.append(os.path.abspath(ct_file))

        if len(ct_paths) == 3:
            rows.append([study] + ct_paths + seg_paths)

    with open(output_csv, "w", newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
            "study",
            "ct_slice1",
            "ct_slice2",
            "ct_slice3",
            "seg_slice1",
            "seg_slice2",
            "seg_slice3"
        ])

        writer.writerows(rows)

    print("CSV créé :", output_csv)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Créer un CSV associant CT et segmentation slices"
    )

    parser.add_argument(
        "--ct_root",
        required=True,
        help="Dossier contenant les slices CT"
    )

    parser.add_argument(
        "--seg_root",
        required=True,
        help="Dossier contenant les slices de segmentation"
    )

    parser.add_argument(
        "--output_csv",
        required=True,
        help="Chemin du CSV de sortie"
    )

    args = parser.parse_args()

    create_atlas_csv(
        args.ct_root,
        args.seg_root,
        args.output_csv
    )
