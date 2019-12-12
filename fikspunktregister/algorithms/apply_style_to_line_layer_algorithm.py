from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
import processing


class ApplyStyleToLineLayerAlgorithm(QgsProcessingAlgorithm):

    def __init__(self, settings):
        QgsProcessingAlgorithm.__init__(self)
        self.settings = settings

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('lag', 'Sæt standard fikspunktregister-symbologi på linie-lag', types=[QgsProcessing.TypeVector], defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        # Sæt stilart til vektorlag
        alg_params = {
            'INPUT': parameters['lag'],
            'STYLE': 'C:\\Users\\kpc\\git\\fire-qgis\\fikspunktregister\\styles\\observation.qml'
        }
        outputs['StStilartTilVektorlag'] = processing.run('qgis:setstyleforvectorlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'apply_line_style'

    def displayName(self):
        return 'Sæt standard fikspunktregister-symbologi på linie-lag'

    def group(self):
        return 'Hjælpe-algoritmer'

    def groupId(self):
        return 'help_algorithms'

    def createInstance(self):
        return ApplyStyleToLineLayerAlgorithm(self.settings)
