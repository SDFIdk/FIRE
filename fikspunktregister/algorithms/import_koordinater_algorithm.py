# -*- coding: utf-8 -*-

__author__ = 'Septima'
__date__ = '2019-12-02'
__copyright__ = '(C) 2019 by Septima'

import os
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon

from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterExpression)

class ImportKoordinaterAlgorithm(QgsProcessingAlgorithm):

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    EXPRESSION = 'EXPRESSION'
    
    def __init__(self, settings):
        QgsProcessingAlgorithm.__init__(self)
        self.settings = settings

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Koordinat-kilde'),
                [QgsProcessing.TypeVector]
            )
        )

        self.addParameter(
            QgsProcessingParameterExpression(
                self.EXPRESSION,
                self.tr('Koordinat-udtryk'),
                parentLayerParameterName = self.INPUT
            )
        )        
        

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, source.fields(), source.wkbType(), source.sourceCrs())

        return {self.OUTPUT: dest_id}

    def name(self):
        return 'fire-import_coordinates'

    def displayName(self):
        return 'Importér koordinater fra FIRE'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ImportKoordinaterAlgorithm(self.settings)

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'ui','fire-export.png')
        return QIcon (icon_path)
