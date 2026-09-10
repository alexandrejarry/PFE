import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
from datetime import datetime


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
        messagebox.showerror(
            "Erreur",
            "Veuillez sélectionner le dossier d'entrée."
        )
        return

    if not output_parent:
        messagebox.showerror(
            "Erreur",
            "Veuillez sélectionner le dossier de sortie."
        )
        return

    # Création du nom avec date et heure
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Création du dossier output
    output_folder = os.path.join(
        output_parent,
        f"output_{timestamp}"
    )

    os.makedirs(output_folder, exist_ok=True)

    command = [
        "nnUNetv2_predict",
        "-i", input_folder,
        "-o", output_folder,
        "-d", "8",
        "-c", "3d_lowres",
    ]

    try:
        status_var.set("Prédiction en cours...")
        root.update()

        subprocess.run(command, check=True)

        status_var.set("Prédiction terminée !")

        messagebox.showinfo(
            "Terminé",
            f"La prédiction est terminée.\n\n"
            f"Résultats enregistrés dans :\n{output_folder}"
        )


        subprocess.run([
            "bash",
            "/home/jarry/Documents/26_SARC/Scripts/mon_script.sh",
            input_folder
        ], check=True)

    except subprocess.CalledProcessError as e:
        status_var.set("Erreur pendant la prédiction.")

        messagebox.showerror(
            "Erreur",
            f"Erreur lors de l'exécution de nnUNet :\n\n{e}"
        )
    

################################################################# Interface #################################################################
 
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