# -*- coding: utf-8 -*-

__author__ = 'Septima'
__date__ = '2019-12-02'
__copyright__ = '(C) 2019 by Septima'

import os
from qgis.core import QgsProcessingProvider
from .algorithms.import_observationer_algorithm import ImportObservationerAlgorithm
from .algorithms.export_observationer_algorithm import ExportObservationerAlgorithm
from .algorithms.import_koordinater_algorithm import ImportKoordinaterAlgorithm

from .settings.settings import Settings

from PyQt5.QtGui import QIcon


class FireProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)
        
        self.settings = Settings()

        self.alglist = [ImportObservationerAlgorithm(self.settings),
                        ExportObservationerAlgorithm(self.settings),
                        ImportKoordinaterAlgorithm(self.settings)]

    def unload(self):
        pass

    def loadAlgorithms(self):
        for alg in self.alglist:
            self.addAlgorithm( alg )

    def id(self):
        return 'fire'

    def name(self):
        return self.tr('Fikspunktregister (SDFE)')

    def longName(self):
        return self.name()

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'fire.svg')
        return QIcon (icon_path)
