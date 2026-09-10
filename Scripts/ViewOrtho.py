import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
import argparse
import os

def ViewOrtho(ct_path, seg_man_path, dataset_path, pred_path, post_path, mv_path, output_root, alpha):
    ct = sitk.ReadImage(ct_path)
    ct = sitk.DICOMOrient(ct, "LAI")
    ct = sitk.RescaleIntensity(ct, 0, 255)  # Normaliser entre 0 et 255
    ct = sitk.Cast(ct, sitk.sitkUInt8)  # Convertir en uint8 pour affichage optimal

    if seg_man_path and seg_man_path != "None":
        has_manual = True
        indices = []
        seg_list = []
        for slices in sorted(os.listdir(seg_man_path)):
            if slices.endswith(".nii.gz"):
                indices.append(int(slices.split("_")[1].replace(".nii.gz", "")))
                seg_path = os.path.join(seg_man_path, slices)
                seg = sitk.ReadImage(seg_path)
                seg = sitk.DICOMOrient(seg, "LAI")
                seg_list.append(seg)
    else:
        has_manual = False
        seg_list = None

    if has_manual:
        if dataset_path and dataset_path != "None":
            dataset = sitk.ReadImage(dataset_path)
            dataset = sitk.DICOMOrient(dataset, "LAI")
        else:
            dataset = None
    else:
        dataset = None

    pred = sitk.ReadImage(pred_path)
    pred = sitk.DICOMOrient(pred, "LAI")

    if not has_manual:
        segmented_slices = []
        for idx in range(ct.GetSize()[2]):
            slice_img = pred[:, :, idx]
            stats = sitk.StatisticsImageFilter()
            stats.Execute(slice_img)
            if stats.GetSum() > 100:  # Minimum 100 pixels segmentés pour éviter les artefacts
                segmented_slices.append(idx)
        if segmented_slices:
            sorted_slices = sorted(segmented_slices)
            middle = sorted_slices[len(sorted_slices) // 2]
            indices = [max(0, middle - 5), middle, min(ct.GetSize()[2] - 1, middle + 5)]
        else:
            indices = [0, ct.GetSize()[2] // 2, ct.GetSize()[2] - 1]

    post = sitk.ReadImage(post_path)
    post = sitk.DICOMOrient(post, "LAI")

    mv = sitk.ReadImage(mv_path)
    mv = sitk.DICOMOrient(mv, "LAI")

    num_cols = 5 if has_manual else 3
    fig, axes = plt.subplots(3, num_cols, figsize=(24, 18))

    for row, idx in enumerate(indices[:3]):
        ct_slice = ct[:, :, idx]
        col = 0
        if has_manual:
            seg_slice = seg_list[row][:,:,0]
            man_mask = sitk.LabelOverlay(ct_slice, seg_slice, opacity=alpha)
            axes[row, col].imshow(np.flipud(sitk.GetArrayFromImage(man_mask)), cmap="jet")
            axes[row, col].set_title(f"Slice {idx} - Manuelle")
            axes[row, col].axis("off")
            col += 1

            dataset_slice = dataset[:, :, idx]
            dataset_mask = sitk.LabelOverlay(ct_slice, dataset_slice, opacity=alpha)
            axes[row, col].imshow(np.flipud(sitk.GetArrayFromImage(dataset_mask)), cmap="jet")
            axes[row, col].set_title(f"Slice {idx} - Dataset")
            axes[row, col].axis("off")
            col += 1

        pred_slice = pred[:, :, idx]
        pred_mask = sitk.LabelOverlay(ct_slice, pred_slice, opacity=alpha)
        axes[row, col].imshow(np.flipud(sitk.GetArrayFromImage(pred_mask)), cmap="jet")
        axes[row, col].set_title(f"Slice {idx} - Prediction")
        axes[row, col].axis("off")
        col += 1

        post_slice = post[:, :, idx]
        post_mask = sitk.LabelOverlay(ct_slice, post_slice, opacity=alpha)
        axes[row, col].imshow(np.flipud(sitk.GetArrayFromImage(post_mask)), cmap="jet")
        axes[row, col].set_title(f"Slice {idx} - Muscle Quality Assessment")
        axes[row, col].axis("off")
        col += 1

        mv_slice = mv[:, :, idx]
        mv_mask = sitk.LabelOverlay(ct_slice, mv_slice, opacity=alpha)
        axes[row, col].imshow(np.flipud(sitk.GetArrayFromImage(mv_mask)), cmap="jet")
        axes[row, col].set_title(f"Slice {idx} - Muscle Volume")
        axes[row, col].axis("off")

    subfolder = "Nouvelles_etudes" if not has_manual else "Etudes_manuelles"
    output_root = os.path.join(output_root, subfolder)

    output_dir = os.path.join(output_root, os.path.basename(ct_path).replace(".nii.gz", ""))
    os.makedirs(output_dir, exist_ok=True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "comparison_slices.png"), dpi=300)
    print("Image sauvegardée : ", output_dir)

def main():

    parser = argparse.ArgumentParser(description="Visualiser les segmentations superposées")
    parser.add_argument("--ct", required=True, help="Chemin vers le volume CT")
    parser.add_argument("--seg", required=False, help="Chemin vers les segmentations manuelles (dossier)")
    parser.add_argument("--dataset", required=True, help="Chemin vers les segmentations du dataset")
    parser.add_argument("--pred", required=True, help="Chemin vers les segmentations prédites")
    parser.add_argument("--post", required=True, help="Chemin vers les  segmentations post-traitées")
    parser.add_argument("--mv", required=True, help="Chemin vers les segmentations de volume musculaire")
    parser.add_argument("--output", required=True, help="Dossier de sortie pour l'image")
    parser.add_argument("--alpha", type=float, default=0.3, help="Transparence des masques (0-1)")  
    args = parser.parse_args()
    ViewOrtho(args.ct, args.seg, args.dataset, args.pred, args.post, args.mv, args.output, args.alpha)

if __name__ == "__main__":
    main()  