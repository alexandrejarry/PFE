import nibabel as nib
import numpy as np
import os

labels_folder = "/opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/Dataset007_Finetune/labelsTr"

mapping = {
    0:0,
    5:1,
    6:2,
    7:3,
    8:4
}

for f in os.listdir(labels_folder):

    if not f.endswith(".nii.gz"):
        continue

    path = os.path.join(labels_folder, f)

    img = nib.load(path)
    seg = img.get_fdata()

    seg = np.rint(seg).astype(int)

    new = np.zeros_like(seg)

    for old, new_label in mapping.items():
        new[seg == old] = new_label

    new = new.astype(np.uint8)

    nib.save(nib.Nifti1Image(new, img.affine), path)

    print(f, "->", np.unique(new))
