# -*- coding: utf-8 -*-
from qgis._core import QgsProcessingParameterVectorDestination

__author__ = "Septima"
__date__ = "2019-12-02"
__copyright__ = "(C) 2019 by Septima"

import os
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon
from qgis.core import (
    QgsProcessing,
    QgsFeatureSink,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterExpression,
    QgsProcessingParameterFileDestination,
    QgsVectorFileWriter,
    QgsProcessingFeatureSource,
)


class ExportObservationerAlgorithm(QgsProcessingAlgorithm):
    OUTPUT = "OUTPUT"
    INPUT = "INPUT"
    EXPRESSION = "EXPRESSION"
    PrmOutputFile = "output_file"

    def __init__(self, settings):
        QgsProcessingAlgorithm.__init__(self)
        self.settings = settings

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT, self.tr("Observationer"), [QgsProcessing.TypeVectorLine]
            )
        )

        # self.addParameter(QgsProcessingParameterFileDestination(
        #    name=self.OUTPUT,
        #    description="Output-fil",
        #   fileFilter = 'csv(*.csv)'
        #   )
        # )

        self.addParameter(
            QgsProcessingParameterVectorDestination(
                name=self.OUTPUT, description="Output"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs(),
        )

        features = source.getFeatures()
        for current, feature in enumerate(features):
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

        # output = self.parameterAsFile(parameters, self.OUTPUT, context)

        # https://qgis.org/pyqgis/3.0/core/Vector/QgsVectorFileWriter.html#qgis.core.QgsVectorFileWriter.writeAsVectorFormat
        # https://books.google.dk/books?id=qLkrDwAAQBAJ&pg=PA375&lpg=PA375&dq=qgis+plugin+write+geojson&source=bl&ots=gJ5UecYDvV&sig=ACfU3U3xmsw4-y7678jgE0PemOekd_vv1g&hl=en&sa=X&ved=2ahUKEwjx27Xaq7LmAhXBGuwKHSflDWoQ6AEwCXoECAoQAQ#v=onepage&q=qgis%20plugin%20write%20geojson&f=false
        # QgsVectorFileWriter.writeAsVectorFormat(layer = source  , filename = output, driverName = "GeoJSON")
        # https://qgis.org/pyqgis/3.0/core/Vector/QgsVectorFileWriter.html#qgis.core.QgsVectorFileWriter.FieldValueConverter

        # features = source.getFeatures()

        # with open(output, 'w') as f:
        #    f.write('<pre>')
        #    for current, feature in enumerate(features):
        #        f.write(str(s))
        #    f.write('</pre>')

        return {self.OUTPUT: dest_id}

    def name(self):
        return "fire-export-observations"

    def displayName(self):
        return "Eksportér observationer til fil"

    def group(self):
        return ""

    def groupId(self):
        return ""

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return ExportObservationerAlgorithm(self.settings)

    def shortHelpString(self):
        return self.tr("Eksportér observationer til fil.")

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "ui", "file-export.png")
        return QIcon(icon_path)
