import sys
from MainWindow import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
import os 
from Devices.zaberClass import Zaber
import threading
from time import gmtime, strftime
class CallStageUI(Ui_MainWindow):
    def __init__(self):
        self.stage = None
        self.distance = None
        self.axisLimits = [0,0,0]
        self.xPos = None
        self.yPos = None
        self.zPos = None
        self.presets = None


    def setUpBtnconnect(self):
        self.connectButton.clicked.connect(self.connectClicked)

        self.upButton.clicked.connect(lambda: self.moveArrow(2,0))
        self.downButton.clicked.connect(lambda:self.moveArrow(2,1))
        self.rightButton.clicked.connect(lambda:self.moveArrow(0,1))
        self.leftButton.clicked.connect(lambda:self.moveArrow(0,0))
        self.closerButton.clicked.connect(lambda:self.moveArrow(1,1))
        self.fartherButton.clicked.connect(lambda:self.moveArrow(1,0))
        self.homeButton.clicked.connect(self.moveHome)
        self.getPositionsButton.clicked.connect(self.getPositions)
        self.setPositionsButton.clicked.connect(self.setPositions)
        self.distanceComboBox.clear()
        distances = ["Custom","0.1", "1","5","10"]
        self.setDistanceLineEdit.setText("2.0")
        self.distance = 2.0
        self.distanceComboBox.addItems(distances)
        self.setDistanceLineEdit.setEnabled(False)
        self.distanceComboBox.currentTextChanged.connect(self.distanceChanged)
        self.setDistanceLineEdit.textEdited.connect(self.customDistanceChanged)

    def enableButtons(self,OnOff = True):
        self.upButton.setEnabled(OnOff)
        self.downButton.setEnabled(OnOff)
        self.leftButton.setEnabled(OnOff)
        self.rightButton.setEnabled(OnOff)
        self.downButton.setEnabled(OnOff)
        self.homeButton.setEnabled(OnOff)
        self.xPositionLineEdit.setEnabled(OnOff)
        self.yPositionLineEdit.setEnabled(OnOff)
        self.zPositionLineEdit.setEnabled(OnOff)
        self.setDistanceLineEdit.setEnabled(OnOff)
        self.getPositionsButton.setEnabled(OnOff)
        self.setPositionsButton.setEnabled(OnOff)
        self.closerButton.setEnabled(OnOff)
        self.fartherButton.setEnabled(OnOff)
        self.distanceComboBox.setEnabled(OnOff)
        self.setDistanceLineEdit.setEnabled(OnOff)


    def distanceChanged(self, t):
        if t == "Custom":
            self.setDistanceLineEdit.setEnabled(True)
            self.distance = float(self.setDistanceLineEdit.text())

        else:
            self.setDistanceLineEdit.setEnabled(False)
            self.distance = float(t)
    def customDistanceChanged(self):
        if self.setDistanceLabel.text() == "":
            self.distance = ""
            return
        try:
            distance = float(self.setDistanceLineEdit.text())
            self.distance = distance
        except:
            self.setDistanceLineEdit.clear()
            self.log("Invalid Input")
    def connectClicked(self):
        threading.Thread(target = self.connectToStage,daemon=True).start()
    def connectToStage(self):
        if self.stage:
            self.stage.closeConnection()
            self.enableButtons(False)
            self.connectButton.setText("Connect")
            self.statusbar.showMessage("Disconnected")
            self.log("Disconnecting")
            self.stage = None
            return
        print("connecting to stage")
        self.log("Connecting to stage")
        stage = Zaber("COM6")
        # res = stage.start()
        res = True
        if res == False:
            self.statusbar.showMessage("Couldn't connect to stage, no serial port available")
            return False
        else:
            self.enableButtons(True)
            self.statusbar.showMessage("Connected")
            self.connectButton.setText("Disconnect")
            self.stage = stage
            for i in range(3):
                self.axisLimits[i] = round(self.stage.getAxisLimit(i),1)
            self.label_2.setText(f"X Position (0-{self.axisLimits[0]})")
            self.label_3.setText(f"Y Position (0-{self.axisLimits[1]})")
            self.label_5.setText(f"Z Position (0-{self.axisLimits[2]})")
            threading.Thread(target = self.getPositions,daemon=True).start()


    def moveArrow(self,axis,direction):
        if self.stage:
            distance = self.distance
            if direction == 0:
                distance *= -1
            self.log(f'moving axis {axis} by {distance} mm')
            try:
                self.stage.move_relative(axis,distance)
                threading.Thread(target = self.getPositions,daemon=True).start()
            except Exception as e:
                
                self.log(e)
                

    def moveHome(self):
        try:
            self.log("Homing")
            self.stage.home_all()
            self.getPositions()

        except Exception as error:
            self.log(error)
            
    def getPositions(self):
        self.xPos, self.yPos, self.zPos = self.stage.get_current_position(0), self.stage.get_current_position(1), self.stage.get_current_position(2)
        self.xPositionLineEdit.setText(str(self.xPos))
        self.yPositionLineEdit.setText(str(self.yPos))
        self.zPositionLineEdit.setText(str(self.zPos))
    def setPositions(self):
        try:
            x,y,z = float(self.xPositionLineEdit.text()),float(self.yPositionLineEdit.text()), float(self.zPositionLineEdit.text())
            self.log(f"Moving to X: {x}, Y: {y}, Z: {z}")
            self.stage.move_absolute_async(x,y,z)
        except Exception as e:
            self.log(e)
            
            
        threading.Thread(target = self.getPositions,daemon=True).start()
    def log(self,message):
        messageSend = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ": " + repr(message)
        print(messageSend)
        self.loggingBrowser.append(messageSend)

        
        

            

    
