# -*- coding: utf-8 -*-

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
                       QgsProcessingFeedback)

from qgis.PyQt.QtCore import (
    QVariant
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

class ImportObservationerByLocationAlgorithm(QgsProcessingAlgorithm):

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
                self.tr('Importér observationer indenfor (within)'),
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
                self.tr('Observationer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback: QgsProcessingFeedback):

        source = self.parameterAsSource(parameters, self.INPUT, context)
        features = source.getFeatures()

        #Felter, der skal gemmes på feature:
        # observation_id String(36)
        # Fikspunkt1_id String(36)
        # Fikspunkt2_id String(36)
        # registrering_fra DateTime
        # koteforskel 
        # nivellementslængde
        # antal opstillinger (value3) Float
        # afstandsafhængig varians (value5 for id=1, value4 for id=2) Float
        # afstandsUafhængig varians (value6 for id=1, value5 for id=2) Float
        # Præcisionsnivellement (value7 for id=1, altid 0 for id=2) Float

        fields = QgsFields()
        fields.append(QgsField("observation_id", QVariant.String))
        fields.append(QgsField("fikspunkt1_id", QVariant.String))
        fields.append(QgsField("fikspunkt2_id", QVariant.String))
        fields.append(QgsField("registrering_fra", QVariant.DateTime))
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

        #Get firedb object
        fire_connection_string = self.settings.value('fire_connection_string')
        fireDb = FireDb(fire_connection_string)

        for current, feature in enumerate(features):
            wkt = feature.geometry().asWkt().upper()
            geometry = Geometry(wkt)
            observations = fireDb.hent_observationer_naer_geometri(geometry, 0)
            feedback.setProgressText('Fandt {antal} observationer'.format(antal = len(observations)))
            points = self.get_points_from_observations(fireDb, observations)
            feedback.setProgressText('Fandt {antal} punkter'.format(antal = len(points)))
            for current, observation in enumerate(observations):
                feature = self.create_feature_from_observation(observation, points)
                if feature: 
                    sink.addFeature(feature, QgsFeatureSink.FastInsert)
                    feedback.setProgressText('En observation blev oprettet for id =  {id}'.format(id = observation.objectid))
                else:
                    feedback.setProgressText('En observation blev IKKE oprettet for id =  {id}'.format(id = observation.objectid))

        return {self.OUTPUT: dest_id}
    
    def create_feature_from_observation(self, observation: Observation, points: Dict[str, Punkt]):
        fikspunkt1_id = observation.opstillingspunktid
        fikspunkt1: Punkt = points[fikspunkt1_id]
        
        fikspunkt2_id = observation.sigtepunktid
        fikspunkt2 = points[fikspunkt2_id]
        
        line_geometry = self.create_line_geometry(fikspunkt1, fikspunkt2)
        if line_geometry:
            # create the feature
            fet = QgsFeature()
            fet.setGeometry(line_geometry)
            #Felter, der skal gemmes på feature:
            #    [QgsField("observation_id", QVariant.String),
            #     QgsField("fikspunkt1_id", QVariant.String),
            #     QgsField("fikspunkt2_id", QVariant.String),
            #     QgsField("registrering_fra", QVariant.DateTime),
            #     QgsField("koteforskel", QVariant.Double),
            #     QgsField("nivellementslaengde", QVariant.Double),
            #     QgsField("antal_opstillinger", QVariant.Double), Value3
            #     QgsField("afstandsafhaengig_varians", QVariant.Double),  (value5 for id=1, value4 for id=2) 
            #     QgsField("afstandsuafhaengig_varians", QVariant.Double),  (value6 for id=1, value5 for id=2) 
            #     QgsField("Praecisionsnivellement", QVariant.Double)],  (value7 for id=1, 0 for id=2) 
            
            observationstypeid = observation.observationstypeid
            observation_id = observation.objectid
            registrering_fra = observation.registreringfra
            koteforskel = observation.value1
            nivellementslaengde = observation.value2
            antal_opstillinger = observation.value3
            if observationstypeid == 1:
                afstandsafhaengig_varians= observation.value5
                afstandsuafhaengig_varians= observation.value6
                Praecisionsnivellement= observation.value7
            elif observationstypeid == 2:
                afstandsafhaengig_varians = observation.value4
                afstandsuafhaengig_varians = observation.value5
                Praecisionsnivellement = 0
            else:
                #observationstypeid > 2
                return None
            
            # create the feature
            feature = QgsFeature()
            feature.setGeometry(line_geometry)
            feature.setAttributes([observation_id,
                               fikspunkt1_id,
                               fikspunkt2_id,
                               registrering_fra,
                               koteforskel,
                               nivellementslaengde,
                               antal_opstillinger,
                               afstandsafhaengig_varians,
                               afstandsuafhaengig_varians,
                               Praecisionsnivellement])
            
            return feature
        else:
            #A geometry could not be established
            return None

    def create_line_geometry(self, punkt1: Punkt, punkt2: Punkt):
        punkt1_k = None
        punkt1_kl: List[Koordinat] =  punkt1.koordinater
        for k in punkt1_kl:
            if k.srid == 'EPSG:4326':
                punkt1_k = k
                
        punkt2_k = None
        punkt2_kl: List[Koordinat] =  punkt2.koordinater
        for k in punkt2_kl:
            if k.srid == 'EPSG:4326':
                punkt2_k = k
        
        if punkt1_k and punkt2_k: 
            wkt = 'LINESTRING ({x1} {y1}, {x2} {y2})'.format(x1 = punkt1_k.x,  y1 = punkt1_k.y, x2 = punkt2_k.x,  y2 = punkt2_k.y)
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
