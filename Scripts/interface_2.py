import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
from datetime import datetime
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
import torch



def select_input_folder():
    folder = filedialog.askdirectory(
        title="Sélectionner le dossier contenant les images"
    )
    if folder:
        input_var.set(folder)

def select_output_folder():
    folder = filedialog.askdirectory(
        title="Sélectionner le dossier de sortie"
    )
    if folder:
        output_var.set(folder)

def run_prediction():

    input_folder = input_var.get()
    output_parent = output_var.get()

    if not input_folder:
        messagebox.showerror("Erreur", "Sélectionnez le dossier d'entrée.")
        return

    if not output_parent:
        messagebox.showerror("Erreur", "Sélectionnez le dossier de sortie.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    output_folder = os.path.join(
        output_parent,
        f"output_{timestamp}"
    )

    os.makedirs(output_folder, exist_ok=True)

    try:

        status_var.set("Initialisation du predictor...")
        root.update()

################################################################# SARC #################################################################

        output_sarc = os.path.join(output_folder, "output_sarc")
        os.makedirs(output_sarc, exist_ok=True)

        predictor_sarc = nnUNetPredictor(
            tile_step_size=0.5,
            use_gaussian=True,
            use_mirroring=True,
            perform_everything_on_device=True,
            device=torch.device("cuda"),
            verbose=False,
            verbose_preprocessing=False,
            allow_tqdm=True
        )

        predictor_sarc.initialize_from_trained_model_folder(
            "/home/jarry/Documents/26_SARC/Dataset008_Finetune/nnUNetTrainer__nnUNetPlans__3d_lowres",
            use_folds=(0, 1, 2, 3, 4),
            checkpoint_name="checkpoint_best.pth"
        )

        status_var.set("Prédiction en cours...")
        root.update()

        predictor_sarc.predict_from_files(
            input_folder,
            output_sarc,
            save_probabilities=False,
            overwrite=True,
            num_processes_preprocessing=2,
            num_processes_segmentation_export=2
        )

################################################################# CTMF #################################################################

        output_ctmf = os.path.join(output_folder, "output_ctmf")
        os.makedirs(output_sarc, exist_ok=True)

        predictor_ctmf = nnUNetPredictor(
            tile_step_size=0.5,
            use_gaussian=True,
            use_mirroring=True,
            perform_everything_on_device=True,
            device=torch.device("cuda"),
            verbose=False,
            verbose_preprocessing=False,
            allow_tqdm=True
        )

        predictor_ctmf.initialize_from_trained_model_folder(
            "/home/jarry/Documents/26_SARC/nnUNetTrainer__nnUNetResEncUNetXLPlans__2d",
            use_folds=(5,),
            checkpoint_name="checkpoint_best.pth"
        )

        status_var.set("Prédiction en cours...")
        root.update()

        predictor_ctmf.predict_from_files(
            input_folder,
            output_ctmf,
            save_probabilities=False,
            overwrite=True,
            num_processes_preprocessing=2,
            num_processes_segmentation_export=2
        )

################################################################# PP #################################################################
        mv = os.path.join(output_folder, "MV")
        os.makedirs(mv, exist_ok=True)

        mqa = os.path.join(output_folder, "MQA")
        os.makedirs(mqa, exist_ok=True)

        subprocess.run([
            "bash",
            "/home/jarry/Documents/26_SARC/Scripts/09_10_post_process.sh",
            output_sarc,
            output_ctmf,
            mv,
            mqa,
        ], check=True)

        status_var.set("Prédiction terminée !")

        messagebox.showinfo(
            "Terminé",
            f"Prédiction terminée.\n\n"
            f"Résultats :\n{output_folder}"
        )

    except Exception as e:

        status_var.set("Erreur")

        messagebox.showerror(
            "Erreur",
            f"Une erreur est survenue :\n\n{e}" 
        )
        
################################################################# Interface #################################################################

if __name__ == "__main__":

    root = tk.Tk()
    root.title("nnUNet Prediction")
    root.geometry("700x280")

    input_var = tk.StringVar()
    output_var = tk.StringVar()
    status_var = tk.StringVar(value="En attente")

    tk.Label(
        root,
        text="Dossier contenant les images :"
    ).pack(
        anchor="w",
        padx=20,
        pady=(20, 5)
    )

    input_frame = tk.Frame(root)
    input_frame.pack(fill="x", padx=20)

    tk.Entry(
        input_frame,
        textvariable=input_var
    ).pack(
        side="left",
        fill="x",
        expand=True
    )

    tk.Button(
        input_frame,
        text="Parcourir...",
        command=select_input_folder
    ).pack(
        side="right",
        padx=(10, 0)
    )

    tk.Label(
        root,
        text="Dossier de sortie :"
    ).pack(
        anchor="w",
        padx=20,
        pady=(15, 5)
    )

    output_frame = tk.Frame(root)
    output_frame.pack(fill="x", padx=20)

    tk.Entry(
        output_frame,
        textvariable=output_var
    ).pack(
        side="left",
        fill="x",
        expand=True
    )

    tk.Button(
        output_frame,
        text="Parcourir...",
        command=select_output_folder
    ).pack(
        side="right",
        padx=(10, 0)
    )

    tk.Button(
        root,
        text="Lancer la prédiction",
        command=run_prediction
    ).pack(pady=25)

    tk.Label(
        root,
        textvariable=status_var
    ).pack()

    root.mainloop()