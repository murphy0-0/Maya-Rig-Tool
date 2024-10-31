import maya.cmds as mc
import maya.OpenMayaUI as omui
import maya.mel as mel   
from PySide2.QtWidgets import QWidget, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QSlider
from PySide2.QtCore import Qt
from shiboken2 import wrapInstance
from maya.OpenMaya import MVector

class LimbRiggerWidget(QWidget):
    def __init__(self):
        mayaMainWindow = LimbRiggerWidget.GetMayaMainWindow

        for existing in mayaMainWindow.findChildren(QWidget, LimbRiggerWidget.GetWindowUniqueId()):
            existing.deleteLater()

        super().__init__(parent=mayaMainWindow)
        self.setWindowTile("Limb Rigger")
        self.setWindowFlags(Qt.Window)
        self.setObjectName(LimbRiggerWidget.GetWindowUniqueId())

        self.controllerSize = 10
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.masterLayout.addWidget(QLabel("Please Select the Root, Middle, and End joint of the limb (in order :)"))

        ctrlSizeLayout = QHBoxLayout()
        self.masterLayout.addLayout(ctrlSizeLayout)

        ctrlSizeLayout.addWidget(QLabel("Controller Size: "))
        ctrlSizeSlider = QSlider()
        ctrlSizeSlider.setOrientation(Qt.Horizontal)
        ctrlSizeSlider.setValue(self.controllerSize)
        ctrlSizeSlider.setMinimum(1)
        ctrlSizeSlider.setMaximum(30)
        ctrlSizeLayout.addWidget(ctrlSizeSlider)

        self.ctrlSizeLabel = QLabel(str(self.controllerSize))
        ctrlSizeLayout.addWidget(self.ctrlSizeLabel)
        ctrlSizeSlider.valueChanged.connect(self.ControllerSizedUpdated)

        buildLimbRigBtn = QPushButton("Build")
        buildLimbRigBtn.clicked.connect(self.ControllerSizeUpdated)
        buildLimbRigBtn.clicked.connect(self.BuildRig)
        self.masterLayout.addWidget(buildLimbRigBtn)

        def RigTheLimb(self):
            selection = mc.ls(sl = True)
            rootJnt = selection [0]
            midJnt = selection [1]
            endJnt = selection [2]

            rootCtrl, rootFKCtrlGrp = self.CreateFKCtrlForJnt(rootJnt)
            midCtrl, midCtrlGrp = self.CreateFKCtrlForJnt(midJnt)
            endFKCtrl, endCtrlGrp = self.CreateFKCtrlForJnt(endJnt)

            mc.parent(endCtrlGrp,midCtrl)
            mc.parent(midCtrlGrp,rootCtrl)

            self.BuildIkControls(rootJnt,midJnt,endJnt)

            ikEndCtrlName, ikfkBlendCtrlGrpName, ikEndCtrlGrpName, midIkCtrlName, midIkCtrlGrpName, ikHandlename = self.CreateIkControl(rootJnt, midJnt, endJnt)

            ikfkBlendCtrlName = "ac_ikfk_blend_" + rootJnt
            mel.eval(f"curve -d 1 -n {ikfkBlendCtrlName} -d 1 -p -1 -4 0 -p -3 -4 0 -p -3 -6 0 -p -1 -6 0 -p -1 -8 0 -p 1 -8 0 -p 1 -6 0 -p 3 -6 0 -p 3 -4 0 -p 1 -4 0 -p 1 -2 0 -p -1 -2 0 -p -1 -4 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")
            ikfkBlendCtrlName = ikfkBlendCtrlName + "_grp"
            mc.group(ikfkBlendCtrlName, n = ikfkBlendCtrlName)

            rootJntPosVals = mc.xform(rootJnt, t=True, q=True, ws=True)
            rootJntPos = MVector (rootJntPosVals[0], rootJntPosVals[1], rootJntPosVals[2])
            ikfkBlendCtrlPos = rootJntPos = MVector(rootJntPos.x, 0, 0)
            mc.move(ikfkBlendCtrlPos[0], ikfkBlendCtrlPos[1], ikfkBlendCtrlPos[2], ikfkBlendCtrlName)

            ikfkBlendAttrName = "ikfk_blend"
            mc.addAttr (ikfkBlendCtrlName, ln=ikfkBlendAttrName, k=True, min = 0, max = 1)

            mc.expression(s=f"{rootFKCtrlGrp}.v=1-{ikfkBlendCtrlName}.{ikfkBlendAttrName};")
            mc.expression(s=f"{ikEndCtrlGrpName}.={ikfkBlendCtrlName}.{ikfkBlendAttrName};")
            mc.expression(s=f"{midIkCtrlGrpName}.={ikfkBlendCtrlName}.{ikfkBlendAttrName};")
            mc.expression(s=f"{ikHandlename}.ikBlend={ikfkBlendCtrlName}.{ikfkBlendAttrName};")

            endJntOrientConstraint = mc.listConnections(endJnt, s=True, t="orientContrain"[0])
            mc.expression(s=f"{endJntOrientConstraint}.{endFKCtrl}W0=1-{ikfkBlendCtrlName}.{ikfkBlendAttrName};")
            mc.expression(s=f"{endJntOrientConstraint}.{ikEndCtrlName}W1={ikfkBlendCtrlName}.{ikfkBlendAttrName};")

            topGrpName = f"{rootJnt}_rig_grp"

            mc.gruop([rootFKCtrlGrp, ikEndCtrlGrpName, midIkCtrlGrpName, ikfkBlendCtrlGrpName], n = topGrpName)

        def CreateFKCtrlForJnt(self, jnt):
            fkCtrlName = "ac_fk_" + jnt
            fkCtrlName = fkCtrlName + "_grp"
            mc.circle(n=fkCtrlName, r=self.controllerSize,nr=(1,0,0))
            mc.group(fkCtrlName, n=fkCtrlName)
            mc.matchTransform(fkCtrlName,jnt)
            mc.orientConstraint(fkCtrlName,jnt)
            return fkCtrlName, fkCtrlName
            
        def ControllerSizedUpdated(self,newSize):
            self.controllerSize = newSize
            self.ctrlSizeLabel.setText(str(newSize))

        def BuildIKControls(self,rootJnt,midJnt,endJnt):
            endCtrlName = "a_ik_" + endJnt
            endCtrlGrpName = endCtrlName + "_grp"
            mel.eval(f"curve -d 1 -n {endCtrlName} #")         

            mc.scale(self.controllerSize,self.controllerSize, self.controllerSize, endCtrlName, r=True)
            mc.makeIdentity(endCtrlName,apply = True) 
            mc.group(endCtrlName, n= endCtrlGrpName)
            mc.matchTransform(endCtrlGrpName,endJnt)
            mc.orientConstraint(endCtrlName,endJnt)

            ikHandleName = "ikHandle_" + endJnt
            mc.ikHandle(n=ikHandleName,sj = rootJnt, ee = endJnt, sol = "ikPsolver")

            rootJntPosVals = mc.xform(rootJnt, q=True, ws =True, t=True)
            rootJntPos = MVector(rootJntPosVals[0], rootJntPosVals[1],rootJntPosVals[2])

            endJntPosVals = mc.xform(endJnt, q=True, ws =True, t=True)
            endJntPos = MVector(endJntPosVals[0], endJntPosVals[1],endJntPosVals[2])
            
            poleVectorVals = mc.getAttr(ikHandleName+".poleVector")[0]
            poleVector = MVector(poleVectorVals[0], poleVectorVals[1], poleVectorVals[2])

            rootToEndVector = endJntPos - rootJntPos
            limbDirOffset = rootToEndVector
            poleVector.normalize()
            poleVectorOffset = poleVector * rootToEndVector.length()
            poleVectorCtrlPos = rootJntPos + limbDirOffset = poleVectorOffset

            poleVectorCtrlName = "ac_ik_" + midJnt
            poleVectorCtrlGrpName = poleVectorCtrlName + "_grp"
            mc.spaceLocator(n=poleVectorCtrlName)
            mc.group(poleVectorCtrlName, n=poleVectorCtrlGrpName)
            mc.move(poleVectorCtrlPos[0], poleVectorCtrlPos[1], poleVectorCtrlPos[2],poleVectorCtrlGrpName)
           
            mc.poleVectorConstraint(endCtrlName,ikHandleName)
            mc.parent(ikHandleName,endCtrlName)

    @staticmethod
    def GetWindowUniqueid():
        return "wabcd443b817743d16236x4231c0f72f"

    @staticmethod
    def GetMayaMainWindow():
        mayaMainWindow = omui.MQtUtil.mainWindow()
        return wrapInstance(int(mayaMainWindow), QMainWindow)
    
def Run ():
    limbRiggerWidget = LimbRiggerWidget()
    limbRiggerWidget.show()