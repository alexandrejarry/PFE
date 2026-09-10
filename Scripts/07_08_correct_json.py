import os
import json

# ----------------------------
# PARAMETRES
# ----------------------------
dataset_name = "08_Dataset008_Finetune_fixed"  # nom du dataset
dataset_dir = dataset_name

imagesTr_dir = os.path.join(dataset_dir, "imagesTr")
labelsTr_dir = os.path.join(dataset_dir, "labelsTr")

file_ending = ".nii.gz"

# ----------------------------
# RECUPERATION DES FICHIERS
# ----------------------------
image_files = sorted([f for f in os.listdir(imagesTr_dir) if f.endswith(file_ending)])
label_files = sorted([f for f in os.listdir(labelsTr_dir) if f.endswith(file_ending)])

identifiers = [os.path.splitext(f)[0].replace("_0000", "") for f in image_files]

# ----------------------------
# CREATION DU JSON
# ----------------------------
dataset_json = {
    "name": dataset_name,
    "description": "",
    "tensorImageSize": "3D",  # ou "2D" si dataset 2D
    "reference": "",
    "licence": "",
    "release": "0.0",
    "modality": {
        "0": "CT"
    },
    "labels": {
        "background": 0,
        "abdo wall": 1,
        "psoas": 2,
        "carre des lombes": 3,
        "erecteurs du rachis + grand dorsal": 4,
    },
    "numTraining": len(label_files),
    "training": [
        {"image": f"./imagesTr/{identifier}_0000{file_ending}", "label": f"./labelsTr/{identifier}{file_ending}"}
        for identifier in identifiers
    ],
    "numTest": 0,
    "test": [],
    "file_ending": file_ending
}

# ----------------------------
# ECRITURE DU FICHIER
# ----------------------------
json_path = os.path.join(dataset_dir, "dataset.json")
with open(json_path, "w") as f:
    json.dump(dataset_json, f, indent=4)

print(f"dataset.json créé pour {dataset_name} à : {json_path}")
