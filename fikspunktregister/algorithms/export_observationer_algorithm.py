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
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterFileDestination)

class ExportObservationerAlgorithm(QgsProcessingAlgorithm):

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    EXPRESSION = 'EXPRESSION'
    PrmOutputFile = 'output_file'
    
    def __init__(self, settings):
        QgsProcessingAlgorithm.__init__(self)
        self.settings = settings

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Observationer'),
                [QgsProcessing.TypeVector]
            )
        )

        self.addParameter(QgsProcessingParameterFileDestination(
            name=self.PrmOutputFile,
            description="Output-fil",
            fileFilter ="xml(*.xml);csv(*.csv);"
            )
        )
        
    def processAlgorithm(self, parameters, context, feedback):
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, source.fields(), source.wkbType(), source.sourceCrs())

        return {self.OUTPUT: dest_id}

    def name(self):
        return 'fire-export-observations'

    def displayName(self):
        return 'Eksportér observationer til fil'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExportObservationerAlgorithm(self.settings)
    
    def shortHelpString(self):
        return self.tr('Eksportér observationer til fil.')

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'ui','file-export.png')
        return QIcon (icon_path)
