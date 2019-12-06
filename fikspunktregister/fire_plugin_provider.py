# -*- coding: utf-8 -*-

__author__ = 'Septima'
__date__ = '2019-12-02'
__copyright__ = '(C) 2019 by Septima'

import os
from qgis.core import QgsProcessingProvider
from .algorithms.import_observationer_by_location import ImportObservationerByLocationAlgorithm
from .algorithms.export_observationer_algorithm import ExportObservationerAlgorithm
from .algorithms.import_punkter_by_punktid_file import ImportPunkterByFilespecAlgorithm
from .algorithms.import_observationer_by_observationid_file import ImportObservationerByFilespecAlgorithm
from .settings.settings import Settings

from PyQt5.QtGui import QIcon


class FireProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)
        
        self.settings = Settings()

        self.alglist = [ImportObservationerByLocationAlgorithm(self.settings),
                        ExportObservationerAlgorithm(self.settings),
                        ImportPunkterByFilespecAlgorithm(self.settings),
                        ImportObservationerByFilespecAlgorithm(self.settings)]

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
