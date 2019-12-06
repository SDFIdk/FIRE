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

class ImportObservationerByFilespecAlgorithm(QgsProcessingAlgorithm):

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
        fire_connection_string = self.settings.value('fire_connection_string')
        
        source = self.parameterAsSource(parameters, self.INPUT, context)
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, source.fields(), source.wkbType(), source.sourceCrs())

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # Add a feature in the sink
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}

    def name(self):
        return 'fire-import-observations-by_filespec'

    def displayName(self):
        return "Importér observationer fra FIRE ud fra liste af observation-id'er"

    def group(self):
        return ''

    def groupId(self):
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ImportObservationerByFilespecAlgorithm(self.settings)
    
    def shortHelpString(self):
        error_message = ''
        fire_connection_string = self.settings.value('fire_connection_string')
        if fire_connection_string is None:
            error_message = "Fejl i konfigurationsfil eller kan ikke finde konfigurationsfil. Se venligst dokumentationen"
        return self.tr("Importerer observationer fra Fikstpunktregistret, hvor id indgår i kilden til punktid'er\n\n" + error_message)

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'ui','fire-export.png')
        return QIcon (icon_path)
