import SimpleITK as sitk
import os
import csv
import argparse


def muscle_surfaces(ct_slice, seg_slice, label):
    """Retourne surface totale, muscle maigre et graisse pour un label"""

    mask = sitk.BinaryThreshold(seg_slice, label, label, 1, 0)
    ct_muscle = sitk.BinaryThreshold(ct_slice, -29, 150, 1, 0) # muscle maigre
    muscle = sitk.Mask(ct_muscle, mask)
    ct_fat = sitk.BinaryThreshold(ct_slice, -190, -30, 1, 0) # graisse intramusculaire
    fat = sitk.Mask(ct_fat, mask)

    stats = sitk.StatisticsImageFilter()
    stats.Execute(muscle)

    muscle_voxels = stats.GetSum()
    stats.Execute(fat)
    fat_voxels = stats.GetSum()
    spacing = ct_slice.GetSpacing()
    pixel_area = spacing[0] * spacing[1]
    muscle_surface = muscle_voxels * pixel_area
    fat_surface = fat_voxels * pixel_area
    total_surface = muscle_surface + fat_surface

    return total_surface, muscle_surface, fat_surface

def fat_surfaces(ct_slice, bf_slice):

    subcutaneous_mask = sitk.BinaryThreshold(bf_slice, 2, 2, 1, 0)
    visceral_mask = sitk.BinaryThreshold(bf_slice, 3, 3, 1, 0)
    intramuscular_mask = sitk.BinaryThreshold(bf_slice, 4, 4, 1, 0)

    stats = sitk.StatisticsImageFilter()
    stats.Execute(subcutaneous_mask)
    subcutaneous_voxels = stats.GetSum()
    stats.Execute(visceral_mask)
    visceral_voxels = stats.GetSum()
    stats.Execute(intramuscular_mask)
    intramuscular_voxels = stats.GetSum()

    spacing = ct_slice.GetSpacing()
    pixel_area = spacing[0] * spacing[1]

    subcutaneous_surface = subcutaneous_voxels * pixel_area
    visceral_surface = visceral_voxels * pixel_area
    intramuscular_surface = intramuscular_voxels * pixel_area

    return [subcutaneous_surface, visceral_surface, intramuscular_surface]


def find_middle_segmented_slice(seg):

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

    return segmented_slices[len(segmented_slices)//2]


def process_study(ct_path, seg_path, bf_path, labels=[1,2,3,4]):

    ct = sitk.ReadImage(ct_path)
    seg = sitk.ReadImage(seg_path)
    bf = sitk.ReadImage(bf_path)
    ct = sitk.DICOMOrient(ct, "LAI")
    seg = sitk.DICOMOrient(seg, "LAI")

    seg = sitk.Resample(
        seg,
        ct,
        sitk.Transform(),
        sitk.sitkNearestNeighbor,
        0,
        seg.GetPixelID()
    )
    bf = sitk.DICOMOrient(bf, "LAI")
    size = ct.GetSize()
    mid_slice = find_middle_segmented_slice(seg)

    if mid_slice is None:
        return None

    ct_slice = sitk.Extract(ct, [size[0],size[1],0], [0,0,mid_slice])
    seg_slice = sitk.Extract(seg, [size[0],size[1],0], [0,0,mid_slice])
    bf_slice = sitk.Extract(bf, [size[0],size[1],0], [0,0,mid_slice])

    results = []

    for label in labels:
        total, muscle, fat = muscle_surfaces(ct_slice, seg_slice, label)
        results.append((total, muscle, fat))

    fats = fat_surfaces(ct_slice, bf_slice)
    return mid_slice, results, fats


def process_dataset(ct_dir, seg_dir, bf_dir, output_csv, labels=[1,2,3,4]):

    ct_files = sorted([f for f in os.listdir(ct_dir) if f.endswith(".nii.gz")])

    with open(output_csv,"w",newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
            "etude",
            "slice",

            "paroi_total","paroi_muscle","paroi_fat",
            "psoas_total","psoas_muscle","psoas_fat",
            "carre_lombes_total","carre_lombes_muscle","carre_lombes_fat",
            "erecteurs_total","erecteurs_muscle","erecteurs_fat",
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

            result = process_study(ct_path, seg_path, bf_path, labels)

            if result is None:
                print("Pas de segmentation:", study)
                continue

            mid_slice, surfaces, fats = result

            row = [study, mid_slice]

            for total, muscle, fat in surfaces:
                row.extend([total, muscle, fat])

            row.extend(fats)
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