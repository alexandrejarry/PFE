import SimpleITK as sitk
import os
import csv
import argparse


def muscle_surface(ct_slice, seg_slice, label):
    """Surface du muscle pour un label donné"""

    mask = sitk.BinaryThreshold(seg_slice, label, label, 1, 0)

    ct_muscle = sitk.BinaryThreshold(ct_slice, -29, 150, 1, 0)
    zone = sitk.Mask(ct_muscle, mask)

    stats = sitk.StatisticsImageFilter()
    stats.Execute(zone)
    voxels = stats.GetSum()

    spacing = zone.GetSpacing()
    pixel_area = spacing[0] * spacing[1]

    return voxels * pixel_area


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



def process_study(ct_path, seg_path, labels=[1,2,3,4]):

    ct = sitk.ReadImage(ct_path)
    seg = sitk.ReadImage(seg_path)

    ct = sitk.DICOMOrient(ct, "LAI")
    seg = sitk.DICOMOrient(seg, "LAI")

    size = ct.GetSize()

    mid_slice = find_middle_segmented_slice(seg)

    if mid_slice is None:
        return None

    ct_slice = sitk.Extract(ct, [size[0],size[1],0], [0,0,mid_slice])
    seg_slice = sitk.Extract(seg, [size[0],size[1],0], [0,0,mid_slice])

    surfaces = []

    for label in labels:
        area = muscle_surface(ct_slice, seg_slice, label)
        surfaces.append(area)

    total = sum(surfaces)

    return mid_slice, surfaces, total


def process_dataset(ct_dir, seg_dir, output_csv, labels=[1,2,3,4]):

    ct_files = sorted([f for f in os.listdir(ct_dir) if f.endswith(".nii.gz")])

    with open(output_csv,"w",newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
            "étude",
            "n° slice",
            "Surface paroi abdominale (mm2)",
            "Surface psoas (mm2)",
            "Surface carré des lombes (mm2)",
            "Surface érecteurs du rachis + gd dorsal (mm2)",
            "SMA (mm2)"
        ])

        for ct_file in ct_files:
            study = ct_file.replace("_0000.nii.gz","")

            ct_path = os.path.join(ct_dir, ct_file)
            seg_file = study + ".nii.gz"
            seg_path = os.path.join(seg_dir, seg_file)

            if not os.path.exists(seg_path):
                print("Segmentation manquante:", study)
                continue

            print("Processing", study)

            result = process_study(ct_path, seg_path, labels)

            if result is None:
                print("Pas de segmentation:", study)
                continue

            mid_slice, surfaces, total = result

            writer.writerow([
                study,
                mid_slice,
                surfaces[0],
                surfaces[1],
                surfaces[2],
                surfaces[3],
                total
            ])

    print("CSV final:", output_csv)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--ct_dir", required=True)
    parser.add_argument("--seg_dir", required=True)
    parser.add_argument("--out_csv", required=True)

    args = parser.parse_args()

    process_dataset(
        args.ct_dir,
        args.seg_dir,
        args.out_csv
    )
