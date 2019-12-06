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

class ImportPunkterByFilespecAlgorithm(QgsProcessingAlgorithm):

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
                self.tr("Kilde til punktid'er"),
                [QgsProcessing.TypeVector]
            )
        )

        self.addParameter(
            QgsProcessingParameterExpression(
                self.EXPRESSION,
                self.tr('punktid-udtryk'),
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
        return 'fire-import_points_by_filespec'

    def displayName(self):
        return "Importér punkter fra FIRE ud fra liste af punktid'er"

    def group(self):
        return ''

    def groupId(self):
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ImportPunkterByFilespecAlgorithm(self.settings)

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'ui','fire-export.png')
        return QIcon (icon_path)

        error_message = ''
        fire_connection_string = self.settings.value('fire_connection_string')
        if fire_connection_string is None:
            error_message = "Fejl i konfigurationsfil eller kan ikke finde konfigurationsfil. Se venligst dokumentationen"
        return self.tr("Importerer punkter fra Fikstpunktregistret, hvor id indgår i kilden til punktid'er\n\n" + error_message)

