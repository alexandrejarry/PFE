import SimpleITK as sitk
import sys

input_file = sys.argv[1]
output_file = sys.argv[2]

img = sitk.ReadImage(input_file)

# détecter les labels présents
stats = sitk.LabelShapeStatisticsImageFilter()
stats.Execute(img)
labels = set(stats.GetLabels())

target_labels = {5,6,7,8}

if labels.intersection(target_labels):

    print("Labels 5-8 détectés → nettoyage + relabelling")

    # garder seulement 5-8
    mask = (
        (img == 5) |
        (img == 6) |
        (img == 7) |
        (img == 8)
    )

    clean = sitk.Mask(img, mask)

    # renommer 5->1, 6->2, 7->3, 8->4
    relabel = (
        sitk.Cast(clean == 5, sitk.sitkUInt8) * 1 +
        sitk.Cast(clean == 6, sitk.sitkUInt8) * 2 +
        sitk.Cast(clean == 7, sitk.sitkUInt8) * 3 +
        sitk.Cast(clean == 8, sitk.sitkUInt8) * 4
    )

    out = sitk.Cast(relabel, sitk.sitkUInt8)

else:

    print("Pas de labels 5-8 → image inchangée")

    # s'assurer que c'est un entier
    out = sitk.Cast(img, sitk.sitkUInt8)

sitk.WriteImage(out, output_file)