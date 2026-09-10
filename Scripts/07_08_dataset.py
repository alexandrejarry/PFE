import os
import shutil
import argparse
import json


def find_segmentation(seg_dir):
    for f in os.listdir(seg_dir):
        if f.endswith(".nii.gz") or f.endswith(".nii"):
            return os.path.join(seg_dir, f)
    return None


def convert_dataset(ct_root, seg_root, output_root):

    imagesTr = os.path.join(output_root, "imagesTr")
    labelsTr = os.path.join(output_root, "labelsTr")

    os.makedirs(imagesTr, exist_ok=True)
    os.makedirs(labelsTr, exist_ok=True)

    ct_files = [f for f in os.listdir(ct_root) if f.endswith(".nii.gz") or f.endswith(".nii")]

    print("Volumes CT trouvés :", len(ct_files))

    case_count = 0

    for ct_file in ct_files:

        case_id = ct_file.replace(".nii.gz", "").replace(".nii", "")

        ct_path = os.path.join(ct_root, ct_file)
        seg_dir = os.path.join(seg_root, case_id)

        if not os.path.isdir(seg_dir):
            print(f"Dossier segmentation manquant : {case_id}")
            continue

        seg_path = find_segmentation(seg_dir)

        if seg_path is None:
            print(f"Aucune segmentation dans {seg_dir}")
            continue

        img_out = os.path.join(imagesTr, case_id + "_0000.nii.gz")
        lab_out = os.path.join(labelsTr, case_id + ".nii.gz")

        shutil.copy(ct_path, img_out)
        shutil.copy(seg_path, lab_out)

        case_count += 1
        print("Ajouté :", case_id)

    # =========================
    # CREATION dataset.json
    # =========================

    dataset_json = {
        "channel_names": {
            "0": "CT"
        },
        "labels": {
            "background": 0,
            "muscle": 1
        },
        "numTraining": case_count,
        "file_ending": ".nii.gz"
    }

    json_path = os.path.join(output_root, "dataset.json")

    with open(json_path, "w") as f:
        json.dump(dataset_json, f, indent=4)

    print("dataset.json créé")
    print("Nombre de cas :", case_count)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--ct", required=True, help="Dossier contenant les volumes CT")
    parser.add_argument("--seg", required=True, help="Dossier contenant les dossiers de segmentation")
    parser.add_argument("--out", required=True, help="Dossier de sortie nnUNet")

    args = parser.parse_args()

    convert_dataset(args.ct, args.seg, args.out)


if __name__ == "__main__":
    main()
