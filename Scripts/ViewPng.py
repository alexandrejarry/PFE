import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import argparse


def overlay_slices(ct_path, seg_path, indices, output, alpha, rotate):

    ct = nib.load(ct_path).get_fdata()
    seg = nib.load(seg_path).get_fdata()

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for i, idx in enumerate(indices):

        if idx < 0 or idx >= ct.shape[2]:
            raise ValueError(f"Slice {idx} hors volume (0-{ct.shape[2]-1})")

        # coupe axiale
        ct_slice = ct[:, :, -idx]
        seg_slice = seg[:, :, -idx]

        if rotate != 0:
            ct_slice = np.rot90(ct_slice, rotate)
            seg_slice = np.rot90(seg_slice, rotate)

        axes[i].imshow(ct_slice, cmap="gray")

        axes[i].imshow(
            np.ma.masked_where(seg_slice == 0, seg_slice),
            cmap="jet",
            alpha=alpha
        )

        axes[i].set_title(f"Axial slice {idx}")
        axes[i].axis("off")

    plt.tight_layout()
    plt.savefig(output, dpi=300)
    print("Image sauvegardée :", output)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--ct", required=True)
    parser.add_argument("--seg", required=True)
    parser.add_argument("--slices", nargs=3, type=int, required=True)
    parser.add_argument("--out", required=True)

    parser.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Transparence du masque (0-1)"
    )

    parser.add_argument(
        "--rotate",
        type=int,
        default=0,
        help="Rotation (0,1,2,3) multipliée par 90°"
    )

    args = parser.parse_args()

    overlay_slices(
        args.ct,
        args.seg,
        args.slices,
        args.out,
        args.alpha,
        args.rotate
    )


if __name__ == "__main__":
    main()
