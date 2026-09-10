#!/bin/bash


#  ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=4 ./04_05_JLF_from_csv.sh /opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/04_slices_CT/batch_1 /opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/04_csv/atlas_pairs_batch_1.csv

#  ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=4 ./04_05_JLF_from_csv.sh /opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/04_slices_CT/batch_2 /opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/04_csv/atlas_pairs_batch_2.csv

#  ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=4 ./04_05_JLF_from_csv.sh /opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/04_slices_CT/batch_3 /opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/04_csv/atlas_pairs_batch_3.csv

#  ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=4 ./04_05_JLF_from_csv.sh /opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/04_slices_CT/batch_4 /opt/UserProjects/25_Sarcopenie_Pialat/0_DataPTI2025/04_csv/atlas_pairs_batch_4.csv




# ==========================
# INPUTS
# ==========================
if [ "$#" -ne 3 ];then
	echo "Usage: $0 <ct_root> <csv_path> <output_root>"
	exit 1
fi

CT_ROOT=$1
CSV_FILE=$2

ANTS_BIN="/opt/Creatis/ANTs/ANTs-Install/bin/antsJointLabelFusion.sh"
OUTPUT_ROOT=$3

mkdir -p "$OUTPUT_ROOT"

# ==========================
# LECTURE CSV
# ==========================

#!TG ATTENTION programme non interruptible .. (for for)
tail -n +2 ${CSV_FILE} | while IFS=',' read -r STUDY CT1 CT2 CT3 SEG1 SEG2 SEG3
do

    #!TG : suppression du caractère \r à la fin de SEG3 (les autres c'est par sécurité)
    #echo -n "${SEG1}" | od -An -tx1 -c
    #echo -n "${SEG2}" | od -An -tx1 -c
    #echo -n "${SEG3}" | od -An -tx1 -c
    SEG1=${SEG1%$'\r'}
    SEG2=${SEG2%$'\r'}
    SEG3=${SEG3%$'\r'}
    #echo -n "${SEG3}" | od -An -tx1 -c

    echo ""
    echo "=============================="
    echo "Processing study: $STUDY"
    echo " Atlases used:"
    echo ${CT1}
    echo "      <--->" ${SEG1}"<>"
    echo ${CT2}
    echo "      <--->" ${SEG2}"<>"
    echo ${CT3}
    echo "      <--->" ${SEG3}"<>"
    echo "=============================="
    

    STUDY_DIR="${CT_ROOT}/${STUDY}"

    if [ ! -d ${STUDY_DIR} ]; then
        echo "CT study not found: ${STUDY_DIR}"
        continue
    fi

    # construire arguments atlas
    ATLAS_ARGS="-g ${CT1} -l ${SEG1} -g ${CT2} -l ${SEG2} -g ${CT3} -l ${SEG3}"

    OUT_STUDY="${OUTPUT_ROOT}/${STUDY}"
    mkdir -p ${OUT_STUDY}

    # ==========================
    # PARCOURIR LES TARGETS
    # ==========================

    for TARGET in "$STUDY_DIR"/*.nii*
    do

        NAME=$(basename ${TARGET})
        NAME=${NAME%.nii.gz}
        NAME=${NAME%.nii}

        echo " ** Segmenting: ${NAME} ** "

        OUT_DIR="${OUT_STUDY}/${NAME}"
        mkdir -p ${OUT_DIR}

        #MY_CMD="${ANTS_BIN} -d 2 -t "${TARGET}" -o "${OUT_DIR}"/ -y s -x otsu ${ATLAS_ARGS}"
        
        ants_args=(
            "-d" "2"
            "-t" "${TARGET}"
            "-o" "${OUT_DIR}/"
            "-y" "s"
            "-x" "otsu"
            "-g" "${CT1}" "-l" "${SEG1}"
            "-g" "${CT2}" "-l" "${SEG2}"
            "-g" "${CT3}" "-l" "${SEG3}"
        )
        ${ANTS_BIN} "${ants_args[@]}"
        #exit #:TG pour tester que le premier        
    done
done

echo "***JLF terminé***"
