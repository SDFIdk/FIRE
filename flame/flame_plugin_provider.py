# -*- coding: utf-8 -*-

__author__ = "Septima"
__date__ = "2019-12-02"
__copyright__ = "(C) 2019 by Septima"

import os
from qgis.core import QgsProcessingProvider
from .algorithms.import_observationer_by_location import (
    ImportObservationerByLocationAlgorithm,
)
from .algorithms.export_observationer_algorithm import ExportObservationerAlgorithm
from .algorithms.apply_style_to_line_layer_algorithm import (
    ApplyStyleToLineLayerAlgorithm,
)
from .algorithms.buffer_in_meters_around_points_algorithm import (
    BufferInMetersAroundPointsAlgorithm,
)
from .settings.settings import Settings

from PyQt5.QtGui import QIcon


class FlameProvider(QgsProcessingProvider):
    def __init__(self):
        QgsProcessingProvider.__init__(self)

        self.settings = Settings()

        self.alglist = [
            ImportObservationerByLocationAlgorithm(self.settings),
            # ExportObservationerAlgorithm(self.settings),
            ApplyStyleToLineLayerAlgorithm(self.settings),
            BufferInMetersAroundPointsAlgorithm(self.settings),
        ]

    def unload(self):
        pass

    def loadAlgorithms(self):
        for alg in self.alglist:
            self.addAlgorithm(alg)

    def id(self):
        return "flame"

    def name(self):
        return self.tr("Flame")

    def longName(self):
        return self.name()

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "fire.svg")
        return QIcon(icon_path)
