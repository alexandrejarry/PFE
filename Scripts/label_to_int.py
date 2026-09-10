import nibabel as nib
import numpy as np
import os
from glob import glob

labels_folder = "/opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/Dataset007_Finetune/labelsTr"
for fpath in glob(os.path.join(labels_folder, "*.nii.gz")):
    img = nib.load(fpath)
    data = img.get_fdata()

    # Arrondi pour obtenir des entiers
    data_int = np.rint(data).astype(np.uint8)  # uint8 si <=255 labels

    # Sauvegarde par-dessus le fichier existant ou dans un nouveau dossier
    nib.save(nib.Nifti1Image(data_int, img.affine, img.header), fpath)

print("Tous les masques ont été convertis en entiers !")
