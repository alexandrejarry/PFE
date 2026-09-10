import SimpleITK as sitk
import numpy as np
import os
import csv
import argparse


def find_segmented_slices(seg):

    size = seg.GetSize()
    segmented_slices = []

    for z in range(size[2]):

        slice_img = sitk.Extract(seg, [size[0], size[1], 0], [0,0,z])

        stats = sitk.StatisticsImageFilter()
        stats.Execute(slice_img)

        if stats.GetMaximum() > 0:
            segmented_slices.append(z)

    if len(segmented_slices) == 0:
        return None

    return segmented_slices


def muscle_volumes_numpy(ct_path, seg_path, bf_path, labels=[1,2,3,4]):

    ct_img = sitk.ReadImage(ct_path)
    seg_img = sitk.ReadImage(seg_path)
    bf_img = sitk.ReadImage(bf_path)

    ct_img = sitk.DICOMOrient(ct_img, "LAI")
    seg_img = sitk.DICOMOrient(seg_img, "LAI")
    bf_img = sitk.DICOMOrient(bf_img, "LAI")

    seg_img = sitk.Resample(
        seg_img,
        ct_img,
        sitk.Transform(),
        sitk.sitkNearestNeighbor,
        0,
        seg_img.GetPixelID()
    )

    bf_img = sitk.Resample(
        bf_img,
        ct_img,
        sitk.Transform(),
        sitk.sitkNearestNeighbor,
        0,
        bf_img.GetPixelID()
    )

    segmented_slices = find_segmented_slices(seg_img)

    if segmented_slices is None:
        return None

    first_slice = segmented_slices[0]
    last_slice = segmented_slices[-1]

    ct = sitk.GetArrayFromImage(ct_img)   # z,y,x
    seg = sitk.GetArrayFromImage(seg_img)
    bf = sitk.GetArrayFromImage(bf_img)

    spacing = ct_img.GetSpacing()
    voxel_volume = spacing[0] * spacing[1] * spacing[2]

    results = []

    # -------- volumes musculaires --------
    for label in labels:

        mask = seg == label

        muscle_mask = mask & (ct >= -29) & (ct <= 150)
        fat_mask = mask & (ct >= -190) & (ct <= -30)

        muscle_voxels = np.sum(muscle_mask)
        fat_voxels = np.sum(fat_mask)

        muscle_volume = muscle_voxels * voxel_volume
        fat_volume = fat_voxels * voxel_volume
        total_volume = muscle_volume + fat_volume

        results.append((total_volume, muscle_volume, fat_volume))

    bf_region = bf[first_slice:last_slice+1]

    fat2_voxels = np.sum(bf_region == 2)
    fat3_voxels = np.sum(bf_region == 3)
    fat4_voxels = np.sum(bf_region == 4)

    fat2_volume = fat2_voxels * voxel_volume
    fat3_volume = fat3_voxels * voxel_volume
    fat4_volume = fat4_voxels * voxel_volume

    return results, fat2_volume, fat3_volume, fat4_volume

def process_dataset(ct_dir, seg_dir, bf_dir, output_csv, labels=[1,2,3,4]):

    ct_files = sorted([f for f in os.listdir(ct_dir) if f.endswith(".nii.gz")])

    with open(output_csv, "w", newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
            "etude",

            "paroi_total_mm3","paroi_muscle_mm3","paroi_fat_mm3",
            "psoas_total_mm3","psoas_muscle_mm3","psoas_fat_mm3",
            "carre_lombes_total_mm3","carre_lombes_muscle_mm3","carre_lombes_fat_mm3",
            "erecteurs_total_mm3","erecteurs_muscle_mm3","erecteurs_fat_mm3",
            "gras souscutané", "gras visceral","gras intramusculaire"
        ])

        for ct_file in ct_files:

            study = ct_file.replace("_0000.nii.gz","")

            ct_path = os.path.join(ct_dir, ct_file)
            seg_path = os.path.join(seg_dir, study + ".nii.gz")
            bf_path = os.path.join(bf_dir, study + ".nii.gz")

            if not os.path.exists(seg_path):
                print("Segmentation manquante:", study)
                continue

            print("Processing", study)

            result = muscle_volumes_numpy(ct_path, seg_path, bf_path, labels)

            if result is None:
                continue

            results, fat2, fat3, fat4 = result

            row = [study]

            for total, muscle, fat in results:
                row.extend([total, muscle, fat])

            row.extend([fat2, fat3, fat4])

            writer.writerow(row)

    print("CSV final:", output_csv)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--ct_dir", required=True)
    parser.add_argument("--seg_dir", required=True)
    parser.add_argument("--bf_dir", required=True)
    parser.add_argument("--out_csv", required=True)

    args = parser.parse_args()

    process_dataset(
        args.ct_dir,
        args.seg_dir,
        args.bf_dir,
        args.out_csv
    )