from processing.gui.wrappers import WidgetWrapper
from .nullable_datetime import NullableDateTimeEdit

class NullableDateTimeWrapper(WidgetWrapper):

    def createWidget(self):
        self._combo = NullableDateTimeEdit()
        return self._combo

    def value(self):
        date_chosen = self._combo.value()
        if date_chosen:
            return date_chosen.toString(Qt.ISODate)
        else:
            return ''