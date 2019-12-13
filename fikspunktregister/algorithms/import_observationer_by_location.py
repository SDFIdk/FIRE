# -*- coding: utf-8 -*-
from fireapi.model.punkttyper import GeometriObjekt

__author__ = 'Septima'
__date__ = '2019-12-02'
__copyright__ = '(C) 2019 by Septima'

import os

from typing import List, Dict

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum,
                       QgsWkbTypes,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsProcessingFeedback,
                       QgsGeometry)

from qgis.PyQt.QtCore import (
    Qt,
    QVariant,
    QDateTime
)
from fireapi import FireDb
from fireapi.model import (
    Geometry,
    Observation,
    Punkt,
    Koordinat
)
from .datetime_widget import DateTimeWidget
from .ui.nullable_datetime_wrapper import NullableDateTimeWrapper

import processing

class ImportObservationerByLocationAlgorithm(QgsProcessingAlgorithm):

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    OBSERVATION_TYPE = 'OBSERVATION_TYPE'
    APPLY_THEME = 'APPLY_THEME'

    def __init__(self, settings):
        QgsProcessingAlgorithm.__init__(self)
        self.settings = settings

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Importér observationer indenfor (within)'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.OBSERVATION_TYPES = [
            ("geometrisk_koteforskel", self.tr("Koteforskel opmålt geometrisk")),
            ("trigonometrisk_koteforskel", self.tr("Koteforskel opmålt trigonometrisk"))]
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.OBSERVATION_TYPE,
                description=self.tr('Observationstype'),
                options=[x[1] for x in self.OBSERVATION_TYPES], 
                allowMultiple = True,
                defaultValue = [0,1]
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
                self.tr('Observationer')
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.APPLY_THEME,
                self.tr('Anvend standard fikspunktregister-symbologi')
            )
        )

    def processAlgorithm(self, parameters, context, feedback: QgsProcessingFeedback):

        feedback.setProgressText('processAlgorithm kaldt med parametre =  =  {parameters}'.format(parameters = str(parameters)))
        source = self.parameterAsSource(parameters, self.INPUT, context)
        
        observation_type = self.parameterAsEnums(parameters, self.OBSERVATION_TYPE, context)

        fields = QgsFields()
        fields.append(QgsField("observation_id", QVariant.String))
        fields.append(QgsField("observation_type_id", QVariant.Double))
        fields.append(QgsField("fikspunkt1_id", QVariant.String))
        fields.append(QgsField("fikspunkt2_id", QVariant.String))
        fields.append(QgsField("registrering_fra", QVariant.DateTime))
        fields.append(QgsField("registrering_fra_iso", QVariant.String))
        fields.append(QgsField("koteforskel", QVariant.Double))
        fields.append(QgsField("nivellementslaengde", QVariant.Double))
        fields.append(QgsField("antal_opstillinger", QVariant.Double))
        fields.append(QgsField("afstandsafhaengig_varians", QVariant.Double))
        fields.append(QgsField("afstandsuafhaengig_varians", QVariant.Double))
        fields.append(QgsField("Praecisionsnivellement", QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            source.sourceCrs())

        fire_connection_string = self.settings.value('fire_connection_string')
        fireDb = FireDb(fire_connection_string)

        features = source.getFeatures()
        for current, feature in enumerate(features):
            wkt = feature.geometry().asWkt().upper()
            geometry = Geometry(wkt)
            observations = fireDb.hent_observationer_naer_geometri(geometry, 0)
            feedback.setProgressText('Fandt {antal} observationer'.format(antal = len(observations)))
            points = self.get_points_from_observations(fireDb, observations)
            feedback.setProgressText('Fandt {antal} punkter'.format(antal = len(points)))
            for current, observation in enumerate(observations):
                feature = self.create_feature_from_observation(observation, points, feedback)
                if feature: 
                    sink.addFeature(feature, QgsFeatureSink.FastInsert)
                    feedback.setProgressText('En observation blev oprettet for id =  {id}'.format(id = observation.objectid))
                else:
                    feedback.setProgressText('En observation blev IKKE oprettet for id =  {id}'.format(id = observation.objectid))
                    
        apply_theme = self.parameterAsBool(parameters, self.APPLY_THEME, context)
        if apply_theme:
            style_file = os.path.join(os.path.dirname(__file__),'..', 'styles','observation.qml')
            alg_params = {
                        'INPUT': dest_id,
                        'STYLE': style_file
                    }
            processing.run('qgis:setstyleforvectorlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        return {self.OUTPUT: dest_id}
    
    def create_feature_from_observation(self, observation: Observation, points: Dict[str, Punkt], feedback: QgsProcessingFeedback):
        observation_id = observation.objectid
        
        fikspunkt1_id = observation.opstillingspunktid
        fikspunkt1: Punkt = points[fikspunkt1_id]
        
        fikspunkt2_id = observation.sigtepunktid
        fikspunkt2 = points[fikspunkt2_id]
        
        line_geometry = self.create_line_geometry(fikspunkt1, fikspunkt2, feedback)
        if line_geometry:
            # create the feature
            fet = QgsFeature()
            fet.setGeometry(line_geometry)
            #Felter, der skal gemmes på feature:
            #    [QgsField("observation_id", QVariant.String),
            #     QgsField("observation_type_id", QVariant.Double)
            #     QgsField("fikspunkt1_id", QVariant.String),
            #     QgsField("fikspunkt2_id", QVariant.String),
            #     QgsField("registrering_fra", QVariant.DateTime),
            #     QgsField("registrering_fra_iso", QVariant.String),
            #     QgsField("koteforskel", QVariant.Double),
            #     QgsField("nivellementslaengde", QVariant.Double),
            #     QgsField("antal_opstillinger", QVariant.Double), Value3
            #     QgsField("afstandsafhaengig_varians", QVariant.Double),  (value5 for id=1, value4 for id=2) 
            #     QgsField("afstandsuafhaengig_varians", QVariant.Double),  (value6 for id=1, value5 for id=2) 
            #     QgsField("Praecisionsnivellement", QVariant.Double)],  (value7 for id=1, 0 for id=2) 
            
            observation_type_id = observation.observationstypeid
            registrering_fra = QDateTime(observation.registreringfra)
            registrering_fra_iso = registrering_fra.toString(Qt.ISODate)
            koteforskel = observation.value1
            nivellementslaengde = observation.value2
            antal_opstillinger = observation.value3
            if observation_type_id == 1:
                afstandsafhaengig_varians= observation.value5
                afstandsuafhaengig_varians= observation.value6
                Praecisionsnivellement= observation.value7
            elif observation_type_id == 2:
                afstandsafhaengig_varians = observation.value4
                afstandsuafhaengig_varians = observation.value5
                Praecisionsnivellement = 0
            else:
                #Observationstypeid > 2
                feedback.setProgressText('observation_type_id > 2 for observation med id =  {id}. Springes over'.format(id = observation_id))
                return None
            
            # create the feature
            feature = QgsFeature()
            feature.setGeometry(line_geometry)
            feature.setAttributes([observation_id,
                               observation_type_id,
                               fikspunkt1_id,
                               fikspunkt2_id,
                               registrering_fra,
                               registrering_fra_iso,
                               koteforskel,
                               nivellementslaengde,
                               antal_opstillinger,
                               afstandsafhaengig_varians,
                               afstandsuafhaengig_varians,
                               Praecisionsnivellement])
            
            return feature
        else:
            #A geometry could not be established
            feedback.setProgressText('En liniegeometri kunne IKKE opettes for observation med id =  {id}'.format(id = observation_id))
            return None

    def create_line_geometry(self, punkt1: Punkt, punkt2: Punkt, feedback: QgsProcessingFeedback):
        punkt1_g: GeometriObjekt = None
        punkt1_gl: List[GeometriObjekt] =  punkt1.geometriobjekter
        if len(punkt1_gl) > 0:
            punkt1_g = punkt1_gl[0] 

        punkt2_g: GeometriObjekt = None
        punkt2_gl: List[GeometriObjekt] =  punkt2.geometriobjekter
        if len(punkt2_gl) > 0:
            punkt2_g = punkt2_gl[0] 

        if punkt1_g and punkt2_g:
            punkt1_k = punkt1_g.geometri._geom['coordinates']
            punkt2_k = punkt2_g.geometri._geom['coordinates']
            wkt = 'LINESTRING ({x1} {y1}, {x2} {y2})'.format(x1 = punkt1_k[0],  y1 = punkt1_k[1], x2 = punkt2_k[0],  y2 = punkt2_k[1])
            geom = QgsGeometry.fromWkt(wkt)
            return geom
        else:
            return None

    def get_points_from_observations(self, fireDb, observations: List[Observation]):
        #returns dict of {id: Punkt}
        points = {}
        for o in observations:
            op_id = o.opstillingspunktid
            if op_id not in points: #Point not already found
                op = fireDb.hent_punkt(op_id)
                points[op_id] = op
            sp_id = o.sigtepunktid
            if sp_id not in points: #Point not already found
                sp = fireDb.hent_punkt(sp_id)
                points[sp_id] = sp
        return points

    def name(self):
        return 'fire-import-observations-location'

    def displayName(self):
        return 'Importér observationer fra FIRE ud fra placering'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def flags(self):
        return QgsProcessingAlgorithm.FlagNoThreading
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ImportObservationerByLocationAlgorithm(self.settings)
    
    def shortHelpString(self):
        error_message = ''
        fire_connection_string = self.settings.value('fire_connection_string')
        if fire_connection_string is None:
            error_message = "Fejl i konfigurationsfil eller kan ikke finde konfigurationsfil. Se venligst dokumentationen"
        return self.tr('Importerer observationer fra Fikstpunktregistret, hvor enten p1 eller p2 er indeholdt i forespørgselsgeometrien\n\n' + error_message)

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'ui','fire-export.png')
        return QIcon (icon_path)
