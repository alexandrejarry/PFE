import logging
import os
from typing import Annotated
import traceback

import vtk
import qt
import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode, vtkMRMLSegmentationNode, vtkMRMLLabelMapVolumeNode
import tempfile
import SimpleITK as sitk
import sitkUtils
import torch
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
import numpy as np


#
# L3Segmentation
#
os.environ["nnUNet_preprocessed"] = "/home/jarry/SSHFS/eq12opt25Sarcopenie/0_DataPTI2025/nnUNet/nnUNet_preprocessed"
os.environ["nnUNet_raw"] = "/home/jarry/SSHFS/eq12opt25Sarcopenie/0_DataPTI2025/nnUNet/nnUNet_raw"
os.environ["nnUNet_results"] = "/home/jarry/SSHFS/eq12opt25Sarcopenie/0_DataPTI2025/nnUNet/nnUNet_results"

class L3Segmentation(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("L3Segmentation")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#L3Segmentation">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # L3Segmentation1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="L3Segmentation",
        sampleName="L3Segmentation1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "L3Segmentation1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="L3Segmentation1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="L3Segmentation1",
    )

    # L3Segmentation2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="L3Segmentation",
        sampleName="L3Segmentation2",
        thumbnailFileName=os.path.join(iconsPath, "L3Segmentation2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="L3Segmentation2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="L3Segmentation2",
    )


#
# L3SegmentationParameterNode
#


@parameterNodeWrapper
class L3SegmentationParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLSegmentationNode
    invertedVolume: vtkMRMLScalarVolumeNode


#
# L3SegmentationWidget
#


class L3SegmentationWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None
        self.seg_sarc_array = None
        self.seg_ctmf_array = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/L3Segmentation.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = L3SegmentationLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        self.pointsSelector = slicer.qMRMLNodeComboBox()
        self.pointsSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.pointsSelector.addEnabled = True
        self.pointsSelector.removeEnabled = True
        self.pointsSelector.noneEnabled = True
        self.pointsSelector.setMRMLScene(slicer.mrmlScene)

        layout = self.ui.pointsSelectorWidget.layout()

        if layout is None:
            layout = qt.QVBoxLayout(self.ui.pointsSelectorWidget)

        layout.addWidget(self.pointsSelector)


        # Buttons
        self.ui.runModelButton.connect("clicked(bool)", self.onApplyButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: L3SegmentationParameterNode | None) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.thresholdedVolume:
            self.ui.runModelButton.toolTip = _("Compute output volume")
            self.ui.runModelButton.enabled = True
        else:
            self.ui.runModelButton.toolTip = _("Select input and output volume nodes")
            self.ui.runModelButton.enabled = False

    def onApplyButton(self):
        print("CLICK DETECTED")

        inputNode = self.ui.inputSelector.currentNode()
        outputNode = self.ui.outputSelector.currentNode()
        outputNode.SetName(inputNode.GetName()+"segmentation")
        pointsSelector = self.pointsSelector


        self.ui.runModelButton.setEnabled(False)
        self.ui.statusLabel.setText("Running nnU-Net...")
        try:
            print("BEFORE RUN")

            self.seg_sarc_array, self.seg_ctmf_array = self.logic.run_nnunet(inputNode, outputNode, pointsSelector)
            self.ui.statusLabel.setText("Done")

            print("AFTER RUN")
            self.onMQAButton()
            self.onMVButton()

        except Exception:
            traceback.print_exc()
            self.ui.statusLabel.setText("Error")

        
        finally:
            self.ui.runModelButton.setEnabled(True)

    def onMQAButton(self):
        inputNode = self.ui.inputSelector.currentNode()
        outputNode = self.ui.outputSelector.addNode()
        outputNode.SetName("MQA")

        self.ui.statusLabel.setText("Applying MQA post-process ... ")

        try:
            print("BEFORE MQA PP")

            self.logic.post_process_mqa(inputNode, self.seg_sarc_array, self.seg_ctmf_array, outputNode)
            self.ui.statusLabel.setText("Done")

            print("AFTER MQA PP")


        except Exception:
            traceback.print_exc()
            self.ui.statusLabel.setText("Error")


        return

    def onMVButton(self):
        inputNode = self.ui.inputSelector.currentNode()
        outputNode = self.ui.outputSelector.addNode()
        outputNode.SetName("MV")

        self.ui.statusLabel.setText("Applying MV post-process ... ")

        try:
            print("BEFORE MV PP")

            self.logic.post_process_mv(inputNode, self.seg_sarc_array, self.seg_ctmf_array, outputNode)
            self.ui.statusLabel.setText("Done")

            print("AFTER MV PP")


        except Exception:
            traceback.print_exc()
            self.ui.statusLabel.setText("Error")

        return
        
    
#
# L3SegmentationLogic
#

class L3SegmentationLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return L3SegmentationParameterNode(super().getParameterNode())
    
    def post_process_mqa(self,inputnode, seg_sarc, seg_ctmf, outputnode):

        pred = sitk.GetImageFromArray(seg_sarc)
        ctmf = sitk.GetImageFromArray(seg_ctmf)

        combined = sitk.Image(pred.GetSize(), sitk.sitkUInt8)
        combined.CopyInformation(pred)

        for seg_label in [1,2,3,4]:
            pred_mask = sitk.BinaryThreshold(pred, seg_label, seg_label, 1, 0)
            vat_mask = sitk.BinaryThreshold(ctmf, 7, 7, 1, 0)
            muscle_fat_mask = sitk.BinaryThreshold(ctmf, 8, 8, 1, 0)

            if seg_label == 1: 
                mask = pred_mask - sitk.And(pred_mask, sitk.Or(vat_mask, muscle_fat_mask))

            elif seg_label in [2,3]:
                mask = pred_mask

            elif seg_label == 4:
                mask = pred_mask - sitk.And(pred_mask, muscle_fat_mask)
                dilated = sitk.BinaryDilate(pred_mask, [3,3,3])
                mask = sitk.Or(dilated, sitk.And(dilated, muscle_fat_mask))

            combined = combined + sitk.Cast(mask, sitk.sitkUInt8) * seg_label

        seg = sitk.GetArrayFromImage(combined)
        predLabelmap = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLLabelMapVolumeNode",
            "Sarcopenia_prediction_MQA"
        )

        slicer.util.updateVolumeFromArray(
            predLabelmap,
            seg
        )

        predLabelmap.SetOrigin(inputnode.GetOrigin())
        predLabelmap.SetSpacing(inputnode.GetSpacing())

        matrix = vtk.vtkMatrix4x4()
        inputnode.GetIJKToRASMatrix(matrix)
        predLabelmap.SetIJKToRASMatrix(matrix)

        segmentation = outputnode.GetSegmentation()
        segmentation.RemoveAllSegments()

        logic = slicer.modules.segmentations.logic()

        logic.ImportLabelmapToSegmentationNode(
            predLabelmap,
            outputnode
        )
        names = [
            "Abdominal wall",
            "Psoas",
            "Quadratus lumborum",
            "Erector spinae",
        ]

        for i in range(segmentation.GetNumberOfSegments()):
            segmentation.GetNthSegment(i).SetName(names[i])

        slicer.mrmlScene.RemoveNode(predLabelmap)

        slicer.util.setSliceViewerLayers(
            background=inputnode,
            )
    
    def post_process_mv(self,inputnode, seg_sarc, seg_ctmf, outputnode ):

        pred = sitk.GetImageFromArray(seg_sarc)
        ctmf = sitk.GetImageFromArray(seg_ctmf)
        combined = sitk.Image(pred.GetSize(), sitk.sitkUInt8)
        combined.CopyInformation(pred)

        for seg_label in [1,2,3,4]:

            pred_mask = sitk.BinaryThreshold(pred, seg_label, seg_label, 1, 0)
            vat_mask = sitk.BinaryThreshold(ctmf, 7, 7, 1, 0)
            muscle_fat_mask = sitk.BinaryThreshold(ctmf, 8, 8, 1, 0)

            if seg_label == 1: 
                mask = pred_mask - sitk.And(pred_mask, sitk.Or(vat_mask, muscle_fat_mask))

            elif seg_label in [2,3]:
                mask = pred_mask

            elif seg_label == 4:
                mask = pred_mask - sitk.And(pred_mask, muscle_fat_mask)

            combined = combined + sitk.Cast(mask, sitk.sitkUInt8) * seg_label
        seg = sitk.GetArrayFromImage(combined)
        predLabelmap = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLLabelMapVolumeNode",
            "Sarcopenia_prediction_MQA"
        )

        slicer.util.updateVolumeFromArray(
            predLabelmap,
            seg
        )

        predLabelmap.SetOrigin(inputnode.GetOrigin())
        predLabelmap.SetSpacing(inputnode.GetSpacing())

        matrix = vtk.vtkMatrix4x4()
        inputnode.GetIJKToRASMatrix(matrix)
        predLabelmap.SetIJKToRASMatrix(matrix)

        segmentation = outputnode.GetSegmentation()
        segmentation.RemoveAllSegments()

        logic = slicer.modules.segmentations.logic()

        logic.ImportLabelmapToSegmentationNode(
            predLabelmap,
            outputnode
        )

        names = [
            "Abdominal wall",
            "Psoas",
            "Quadratus lumborum",
            "Erector spinae",
        ]

        for i in range(segmentation.GetNumberOfSegments()):
            segmentation.GetNthSegment(i).SetName(names[i])
    

        slicer.mrmlScene.RemoveNode(predLabelmap)

        slicer.util.setSliceViewerLayers(
            background=inputnode,
            )
        
    def run_nnunet_api(self, inputVolume, outputNode, pointsSelector):

        # 1. temp workspace
        workdir = tempfile.mkdtemp()
        input_dir = os.path.join(workdir, "input")
        output_dir = os.path.join(workdir, "output")
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # 2. Slicer → NIfTI
        input_path = os.path.join(input_dir, "case_0000_0000.nii.gz")
        img = sitkUtils.PullVolumeFromSlicer(inputVolume)
        sitk.WriteImage(img, input_path)

        # 3. CREATE PREDICTOR
        predictor_sarc = nnUNetPredictor(
            tile_step_size=1,
            use_gaussian=True,
            use_mirroring=True,
            perform_everything_on_device=False,  # CPU safe
            device=torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"),
            verbose=True,
            verbose_preprocessing=True,
            allow_tqdm=True
        )

        predictor_ctmf = nnUNetPredictor(
            tile_step_size=1,
            use_gaussian=True,
            use_mirroring=True,
            perform_everything_on_device=False,  # CPU safe
            device=torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"),
            verbose=True,
            verbose_preprocessing=True,
            allow_tqdm=True
        )

        # 4. LOAD MODEL
        model_folder_sarc = "/home/jarry/Documents/26_SARC/Dataset008_Finetune/nnUNetTrainer__nnUNetPlans__3d_lowres"
        modelf_folder_ctmf = "/home/jarry/Documents/26_SARC/nnUNetTrainer__nnUNetResEncUNetXLPlans__2d"
        print("A - BEFORE INIT")

        try:
            predictor_sarc.initialize_from_trained_model_folder(
                model_folder_sarc,
                use_folds=(0,),
                checkpoint_name="checkpoint_final.pth"
            )

            predictor_ctmf.initialize_from_trained_model_folder(
                modelf_folder_ctmf,
                use_folds=(5,),
                checkpoint_name="checkpoint_final.pth"
            )

            print("B - AFTER INIT")

        except Exception as e:
            print("Exception:")
            traceback.print_exc()

        img_sitk = sitkUtils.PullVolumeFromSlicer(inputVolume)
        img_np = sitk.GetArrayFromImage(img_sitk)  # (Z, Y, X)
        img_np = img_np[None, ...].astype(np.float32)

        # 5. RUN INFERENCE
        print("C - BEFORE PREDICT")


        # ============================================================
        # Volume numpy : (Z, Y, X)
        # ============================================================

        img_np = sitk.GetArrayFromImage(img_sitk)

        print("Shape image originale :", img_np.shape)

        # ============================================================
        # Récupération des deux points
        # ============================================================

        pointsNode = pointsSelector.currentNode()

        if pointsNode is None:
            raise ValueError("Aucun node de points sélectionné.")

        if pointsNode.GetNumberOfControlPoints() < 2:
            raise ValueError("Il faut placer au moins deux points.")

        # Coordonnées RAS
        p1_ras = [0.0, 0.0, 0.0]
        p2_ras = [0.0, 0.0, 0.0]

        pointsNode.GetNthControlPointPositionWorld(0, p1_ras)
        pointsNode.GetNthControlPointPositionWorld(1, p2_ras)

        print("Point 1 RAS :", p1_ras)
        print("Point 2 RAS :", p2_ras)

        # ============================================================
        # Conversion RAS -> IJK
        # ============================================================

        ras_to_ijk = vtk.vtkMatrix4x4()
        inputVolume.GetRASToIJKMatrix(ras_to_ijk)

        p1_ijk = [0.0, 0.0, 0.0, 1.0]
        p2_ijk = [0.0, 0.0, 0.0, 1.0]

        ras_to_ijk.MultiplyPoint(
            [p1_ras[0], p1_ras[1], p1_ras[2], 1.0],
            p1_ijk
        )

        ras_to_ijk.MultiplyPoint(
            [p2_ras[0], p2_ras[1], p2_ras[2], 1.0],
            p2_ijk
        )

        print("Point 1 IJK :", p1_ijk)
        print("Point 2 IJK :", p2_ijk)

        # ============================================================
        # On utilise uniquement Z
        # ============================================================

        z1 = int(round(p1_ijk[2]))
        z2 = int(round(p2_ijk[2]))

        z_min = min(z1, z2)
        z_max = max(z1, z2)

        print(f"Zone étudiée : {z_min} -> {z_max}")

        # ============================================================
        # Vérification
        # ============================================================

        num_slices = img_np.shape[0]

        print("Nombre de slices :", num_slices)

        if z_min < 0 or z_max >= num_slices:
            raise ValueError(
                f"Zone Z invalide : {z_min} -> {z_max} "
                f"pour un volume de {num_slices} slices."
            )

        # ============================================================
        # Extraction de la ROI
        # ============================================================

        img_roi = img_np[z_min:z_max + 1, :, :]
        # Ajout de la dimension canal pour nnU-Net
        img_roi = img_roi[np.newaxis, ...]


        print("Shape volume original :", img_np.shape)
        print("Shape volume ROI      :", img_roi.shape)


        properties = {
            "spacing": img_sitk.GetSpacing()[::-1],  # SITK (X,Y,Z) -> nnUNet (Z,Y,X)
            "origin": img_sitk.GetOrigin()[::-1],
            "direction": np.array(img_sitk.GetDirection()).reshape(3,3)[::-1, ::-1],
        }

        seg_sarc = predictor_sarc.predict_single_npy_array(
            img_roi,
            properties,
            None
        )
        seg_sarc = np.array(seg_sarc) # securité gpu
        seg_sarc = np.squeeze(seg_sarc)  # (Z,Y,X)

        seg_ctmf = predictor_ctmf.predict_single_npy_array(
            img_roi,
            properties,
            None
        )
        seg_ctmf = np.array(seg_ctmf) # securité gpu
        seg_ctmf = np.squeeze(seg_ctmf)  # (Z,Y,X)

        seg_ctmf[seg_ctmf == 1] = 5
        seg_ctmf[seg_ctmf == 2] = 6
        seg_ctmf[seg_ctmf == 3] = 7
        seg_ctmf[seg_ctmf == 4] = 8

########################################################## superposition de la segmentation ####################################################################################

        full_seg_sarc = np.zeros(
            img_np.shape,
            dtype=np.uint8
        )

        full_seg_ctmf = np.zeros(
            img_np.shape,
            dtype=np.uint8
        )

        # On replace la ROI à sa position originale
        full_seg_sarc[z_min:z_max + 1, :, :] = seg_sarc
        full_seg_ctmf[z_min:z_max + 1, :, :] = seg_ctmf

        print("Segmentation complète sarc :", full_seg_sarc.shape)
        print("Segmentation complète CTMF :", full_seg_ctmf.shape)

        predLabelmap = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLLabelMapVolumeNode",
            "Sarcopenia_prediction"
        )

        ctmfLabelmap = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLLabelMapVolumeNode",
            "CTMF_prediction"
        )

        slicer.util.updateVolumeFromArray(
            predLabelmap,
            full_seg_sarc
        )

        slicer.util.updateVolumeFromArray(
            ctmfLabelmap,
            full_seg_ctmf
        )
  
        # synchronisation spatiale
        predLabelmap.SetOrigin(inputVolume.GetOrigin())
        predLabelmap.SetSpacing(inputVolume.GetSpacing())

        matrix = vtk.vtkMatrix4x4()
        inputVolume.GetIJKToRASMatrix(matrix)
        predLabelmap.SetIJKToRASMatrix(matrix)

        ctmfLabelmap.SetOrigin(inputVolume.GetOrigin())
        ctmfLabelmap.SetSpacing(inputVolume.GetSpacing())

        matrix = vtk.vtkMatrix4x4()
        inputVolume.GetIJKToRASMatrix(matrix)
        ctmfLabelmap.SetIJKToRASMatrix(matrix)

        segmentation = outputNode.GetSegmentation()
        segmentation.RemoveAllSegments()

        logic = slicer.modules.segmentations.logic()

        logic.ImportLabelmapToSegmentationNode(
            predLabelmap,
            outputNode
        )

        logic.ImportLabelmapToSegmentationNode(
            ctmfLabelmap,
            outputNode
        )

        names = [
            "Abdominal wall",
            "Psoas",
            "Quadratus lumborum",
            "Erector spinae",
            "All muscles",
            "SAT",
            "VAT",
            "Muscle fat"
        ]

        for i in range(segmentation.GetNumberOfSegments()):
            segmentation.GetNthSegment(i).SetName(names[i])

        slicer.mrmlScene.RemoveNode(predLabelmap)
        slicer.mrmlScene.RemoveNode(ctmfLabelmap)
        slicer.util.setSliceViewerLayers(
            background=inputVolume,
            )

        print("D - AFTER PREDICT")

        return full_seg_sarc, full_seg_ctmf
    
    def run_nnunet(self, inputVolume, outputNode, pointsSelector):
        print("RUNNING NNUNET")
        return self.run_nnunet_api(inputVolume, outputNode, pointsSelector)


    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLLabelMapVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "InputVolume": inputVolume.GetID(),
            "OutputVolume": outputVolume.GetID(),
            "ThresholdValue": imageThreshold,
            "ThresholdType": "Above" if invert else "Below",
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")


#
# L3SegmentationTest
#


class L3SegmentationTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_L3Segmentation1()

    def test_L3Segmentation1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("L3Segmentation1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = L3SegmentationLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
