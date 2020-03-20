from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt.QtWidgets import QDateTimeEdit
from qgis.PyQt.QtCore import QCoreApplication, QDate

class DateTimeWidget(WidgetWrapper):

    def createWidget(self):
        self._combo = QDateTimeEdit()
        self._combo.setCalendarPopup(True)

        return self._combo

    def value(self):
        date_chosen = self._combo.dateTime()
        return date_chosen.toString(Qt.ISODate)