import maya.cmds as mc
import maya.OpenMayaUI as omui
import maya.mel as mel   
from PySide2.QtWidgets import QWidget, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QSlider, QGridLayout
from PySide2.QtCore import Qt
from shiboken2 import wrapInstance
from maya.OpenMaya import MVector

class TrimSheetBuilderWidget(QWidget):
    def __init__(self):
        mayaMainWindow = TrimSheetBuilderWidget.GetMayaMainWindow

        for existing in mayaMainWindow.findChildren(QWidget, TrimSheetBuilderWidget.GetWindowUniqueId()):
            existing.deleteLater()

        super().__init__(parent=mayaMainWindow)
        self.setWindowTile("Limb Rigger")
        self.setWindowFlags(Qt.Window)
        self.setObjectName(TrimSheetBuilderWidget.GetWindowUniqueId())

        self.controllerSize = 10
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)    

        self.shell = []
        self.CreateInitialiationSection()
        self.CreateManipulationSection()
        
    def FillShellToU1V1(self):
        width, height = self.GetShellSize()
        su = 1 / width
        sv = 1 / height
        self.Scalehell(su, sv)
        self.MoveToOrigin()

    def GetShellSize(self):
        min, max = self.GetShellBounds()
        height = max[1] - min[1]
        width = max[0] - min[1]

        return width, height
    
    def ScaleShell (self, u, v):
        mc.polyEditUV(self.shell, su = v, sv = v, r=True)
    
    def CreateManipulationSection(self):
        sectionLayout = QVBoxLayout()
        self.masterLayout.addWidget(sectionLayout)

        turnBtm = QPushButton ("Turn")
        turnBtm.clicked.connet(self.TunShell)
        sectionLayout.addWidget(turnBtm)

        backToOriginBtm = QPushButton ("Back To Origin")
        backToOriginBtm.clicked.connect(self.MoveShellToOrigin)
        sectionLayout.addWidget(backToOriginBtm)

        fillU1V1Btn = QPushButton("Fill UV")
        fillU1V1Btn.click.connect(self.FillShellToU1V1)
        sectionLayout.addWidget(fillU1V1Btn)

        halfUBtn = QPushButton("Half U")
        halfUBtn.clicked.connect(lambda : self.ScaleShell(0.5, 1))
        sectionLayout.addWidget(halfUBtn)

        halfVBtn = QPushButton("Half V")
        halfVBtn.clicked.connect(lambda : self.ScaleShell(1, 0.5))
        sectionLayout.addWidget(halfVBtn)

        doubleUBtn = QPushButton("Double U")
        doubleUBtn.clicked.connect(lambda : self.ScaleShell(0.5, 1))
        sectionLayout.addWidget(doubleUBtn)

        doubleVBtn = QPushButton("Double V")
        doubleVBtn.clicked.connect(lambda : self.ScaleShell(1, 0.5))
        sectionLayout.addWidget(doubleVBtn)

        moveSection = QGridLayout()
        sectionLayout.addLayout(moveSection)

        moveUpBtn = QPushButton("^")
        moveUpBtn.clicked.connect(lambda : self.MoveShell(0, 1))
        moveSection.addWidget(moveUpBtn, 0, 1)

        moveDownBtn = QPushButton("V")
        moveDownBtn.clicked.connect(lambda : self.MoveShell(0, -1))
        moveSection.addWidget(moveDownBtn, 2, 1)

        moveLeftBtn = QPushButton("<")
        moveLeftBtn.clicked.connect(lambda : self.MoveShell(-1, 0))
        moveSection.addWidget(moveLeftBtn, 1, 0)

        moveRightBtn = QPushButton(">")
        moveRightBtn.clicked.connect(lambda : self.MoveShell(1, 0))
        moveSection.addWidget(moveRightBtn, 1, 2)

    def GetShellBounds(self):
        uvs =mc.polyListComponentConversion(self.shell, toUV = True)
        uvs = mc.ls(uvs, fl=True)
        firstUV = mc.polyEditUV(uvs[0], q = True)
        minU = firstUV[0]
        maxU = firstUV[0]
        minV = firstUV[1]
        maxV = firstUV[1]

        for uv in uvs:
            uvCoord = mc.polyEditUV(uv, q=True)
            if uvCoord[0] < minU:
                minU = uvCoord[0]

            if uvCoord[0] > maxU:
                minU = uvCoord[0]

            if uvCoord[1] < minV:
                minU = uvCoord[1]

            if uvCoord[1] > maxV:
                minU = uvCoord[1]
        return [minU, minV], [maxU, maxV]

    def BackToOrigin(self):
        minCoord, maxCoord = self.GetShellBounds()
        mc.polyEditUV(self.shell, u=-minCoord[0], v=-minCoord[1])

    def TurnShell(self):
        mc.select(self.shell, r=True)
        mel.eval("polyRoateUVs 90 0")

    def MoveShell(self, u, v):
        width, height = self.GetShellSize()
        uAmt = u * width
        vAmnt = v * height

    def CreateInitialiationSection(self):
        sectionLayout = QHBoxLayout()
        self.masterLayout.addLayout(sectionLayout)

        selectShellBtm = QPushButton("Select Shell")
        selectShellBtm.clicked.connect(self.SelectShell)

        unfoldBtm = QPushButton("Unfold")
        unfoldBtm.clicked.connect(self.UnfoldShell)
        sectionLayout.addWidget(unfoldBtm)

        cutAndUnfoldBtm = QPushButton("Cut and Unfold")
        cutAndUnfoldBtm.clicked.connect(self.CutAndUnfoldShell)

        unitizeBtn = QPushButton("Unitize")
        unitizeBtn.clicked.connect(self.UnitizeShell)
        sectionLayout.addWidget(unitizeBtn)

    def UnitizeShell(self):
        edges = mc.polyListComponentConversion(self.shell, toEde=True)
        edges = mc.ls(edges, fl = True)
        
        sewedEdges = []
        for edge in edges:
            vertices = mc.polyListComponentConversion(edge, toVertex=True)
            
            UVs = mc.poluListComponentConversion(edge, toUV = True)
            UVs = mc.ls(UVs, fl = True)

            if len(UVs) == len(vertices):
                sewedEdges.append(edge)

        mc.polyForceUV(self.shell, unitize=True)
        mc.polyMapSewMove(sewedEdges)
        mc.u3dLayout(self.shell)

    def SelectShell(self):
        edges = mc.ls(sl=True)
        mc.polyProjection(self.shell, type="Planar", md="c")
        mc.polyMapCut(edges)
        mc.u3dUnfold(self.shell)
        mel.eval("textOrientShells")


    @staticmethod
    def GetWindowUniqueid():
        return "cbbee573b817707d16006e4231c0d72f"

    @staticmethod #decorator
    def GetMayaMainWindow():
        mayaMainWindow = omui.MQtUtil.mainWindow()
        return wrapInstance(int(mayaMainWindow), QMainWindow)

def Run():  
    TrimSheetBuilderWidget().show()