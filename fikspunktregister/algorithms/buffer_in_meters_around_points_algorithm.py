import os
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterDistance
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsCoordinateReferenceSystem
import processing


class BufferInMetersAroundPointsAlgorithm(QgsProcessingAlgorithm):

    def __init__(self, settings):
        QgsProcessingAlgorithm.__init__(self)
        self.settings = settings

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterDistance('buffer', 'Buffer i meter', parentParameterName='', minValue=2, maxValue=50, defaultValue=10))
        self.addParameter(QgsProcessingParameterFeatureSource('punkter2', 'Om disse punkter', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('BufferOmValgtePunkter', 'Buffer om valgte punkter', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True ))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}

        # Reprojektér lag
        alg_params = {
            'INPUT': parameters['punkter2'],
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:25832'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojektrLag'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        # Konkavt hul (alfa-form)
        alg_params = {
            'ALPHA': 1,
            'HOLES': False,
            'INPUT': outputs['ReprojektrLag']['OUTPUT'],
            'NO_MULTIGEOMETRY': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['KonkavtHulAlfaform'] = processing.run('qgis:concavehull', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': parameters['buffer'],
            'END_CAP_STYLE': 0,
            'INPUT': outputs['KonkavtHulAlfaform']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        # Reprojektér lag
        alg_params = {
            'INPUT': outputs['Buffer']['OUTPUT'],
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'OUTPUT_': parameters['BufferOmValgtePunkter'],
            'OUTPUT__': 'memory:Buffer',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        #result = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        #return result
        outputs['ReprojektrLag'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 0,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['ReprojektrLag']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': parameters['BufferOmValgtePunkter']
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        #Virker
        #results['BufferOmValgtePunkter'] = outputs['ReprojektrLag']['OUTPUT']
        #return results
        style_file = os.path.join(os.path.dirname(__file__),'..', 'styles','buffer.qml')
        alg_params = {
                    'INPUT': outputs['Buffer']['OUTPUT'],
                    'STYLE': style_file
                }
        processing.run('qgis:setstyleforvectorlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)


        # Omdøb lag
        #Virker ikke, men læs følgende link
        #Se https://gis.stackexchange.com/questions/280740/using-temporary-layer-as-input-for-other-algorithm-in-processing-script
        alg_params = {
            'INPUT': outputs['Buffer']['OUTPUT'],
            'NAME': 'Buffer om punkter'
        }
        outputs['OmdbLag'] = processing.run('native:renamelayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        
        results['BufferOmValgtePunkter'] = outputs['ReprojektrLag']['OUTPUT']
        return results
 
    def name(self):
        return 'buffer_around_points'

    def displayName(self):
        return 'Buffer i meter om punkter'

    def group(self):
        return 'Hjælpe-algoritmer'

    def groupId(self):
        return 'help_algorithms'

    def createInstance(self):
        return BufferInMetersAroundPointsAlgorithm(self.settings)
