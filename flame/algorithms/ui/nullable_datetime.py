import os
from PyQt5.QtWidgets import *
from PyQt5 import uic


WIDGET, _ = uic.loadUiType(
    os.path.join(
        os.path.dirname(__file__),
        'nullable_datetime.ui'
    )
)

class NullableDateTimeEdit(QWidget, WIDGET):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.setupUi(self)
        self.checkBox.stateChanged.connect(self.checkbox_statechanged)
        self.dateTimeEdit.setEnabled(self.checkBox.isChecked())
        
    def checkbox_statechanged(self):
        self.dateTimeEdit.setEnabled(self.checkBox.isChecked())
        
    def value(self):
        if self.checkBox.isChecked():
            date = self.dateTimeEdit.dateTime()
            return date
        else:
            return None