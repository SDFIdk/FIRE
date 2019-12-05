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
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum)

from .datetime_widget import DateTimeWidget
from .ui.nullable_datetime_wrapper import NullableDateTimeWrapper

class ImportObservationerAlgorithm(QgsProcessingAlgorithm):

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    OBSERVATION_TYPE = 'OBSERVATION_TYPE'

    def __init__(self, settings):
        QgsProcessingAlgorithm.__init__(self)
        self.settings = settings

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Indlæs observationer indenfor (within)'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.OBSERVATION_TYPES = [("type1", self.tr("Type 1")), ("type2", self.tr("Type 2"))]
        self.addParameter(
            QgsProcessingParameterEnum(
                self.OBSERVATION_TYPE,
                self.tr('Observationstype'),
                options=[x[1] for x in self.OBSERVATION_TYPES], 
                allowMultiple = True
            )
        )


        param = QgsProcessingParameterString(name = 'from_date', description = 'Fra Dato', optional = True)
        param.setMetadata({
            'widget_wrapper': {
                'class': NullableDateTimeWrapper}})
        self.addParameter(param)
        
        param = QgsProcessingParameterString(name = 'to_date', description = 'Til Dato', optional = True)
        param.setMetadata({
            'widget_wrapper': {
                'class': NullableDateTimeWrapper}})
        self.addParameter(param)
        
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
        return 'fire-import-observations'

    def displayName(self):
        return 'Indlæs observationer fra FIRE'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ImportObservationerAlgorithm(self.settings)
    
    def shortHelpString(self):
        error_message = ''
        fire_connection_string = self.settings.value('fire_connection_string')
        if fire_connection_string is None:
            error_message = "Fejl i konfigurationsfil eller kan ikke finde konfigurationsfil. Se venligst dokumentationen"
        return self.tr('Importerer observationer fra Fikstpunktregistret, hvor enten p1 eller p2 er indeholdt i forespørgselsgeometrien\n\n' + error_message)

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'ui','fire-export.png')
        return QIcon (icon_path)
