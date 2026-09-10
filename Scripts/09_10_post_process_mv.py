import SimpleITK as sitk
import os
import argparse

def post_process(pred_path, ctmf_path, out_dir):

    os.makedirs(out_dir, exist_ok=True)

    pred = sitk.ReadImage(pred_path)
    ctmf = sitk.ReadImage(ctmf_path)

    pred = sitk.DICOMOrient(pred, "LAI")
    ctmf = sitk.DICOMOrient(ctmf, "LAI")

    combined = sitk.Image(pred.GetSize(), sitk.sitkUInt8)
    combined.CopyInformation(pred)

    for seg_label in [1,2,3,4]:

        pred_mask = sitk.BinaryThreshold(pred, seg_label, seg_label, 1, 0)

        vat_mask = sitk.BinaryThreshold(ctmf, 3, 3, 1, 0)
        muscle_fat_mask = sitk.BinaryThreshold(ctmf, 4, 4, 1, 0)

        if seg_label == 1: 
            mask = pred_mask - sitk.And(pred_mask, sitk.Or(vat_mask, muscle_fat_mask))

        elif seg_label in [2,3]:
            mask = pred_mask

        elif seg_label == 4:
            mask = pred_mask - sitk.And(pred_mask, muscle_fat_mask)

        combined = combined + sitk.Cast(mask, sitk.sitkUInt8) * seg_label
        
    basename = os.path.basename(pred_path)
    sitk.WriteImage(combined, os.path.join(out_dir,basename))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post-process segmentation to compute fat/muscle areas")
    parser.add_argument("--pred", required=True, help="Path to prediction NIfTI")
    parser.add_argument("--ctmf", required=True, help="Path to CTMF NIfTI")
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()

    post_process(args.pred, args.ctmf, args.out)