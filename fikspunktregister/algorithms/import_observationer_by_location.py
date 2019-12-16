# -*- coding: utf-8 -*-
from fireapi.model.punkttyper import GeometriObjekt

__author__ = 'Septima'
__date__ = '2019-12-02'
__copyright__ = '(C) 2019 by Septima'

import os
from datetime import datetime

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
                       QgsGeometry,
                       QgsProject)

from qgis.PyQt.QtCore import (
    Qt,
    QVariant,
    QDateTime
)
try:
    from fireapi import FireDb
except:
    FireDb = None
    
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
    FROM_DATE = 'FROM_DATE'
    TO_DATE = 'TO_DATE'

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
            (1, self.tr("Koteforskel opmålt geometrisk")),
            (2, self.tr("Koteforskel opmålt trigonometrisk"))]
        
        o = QgsProcessingParameterEnum(
                name=self.OBSERVATION_TYPE,
                description=self.tr('Observationstype'),
                options=[x[1] for x in self.OBSERVATION_TYPES], 
                allowMultiple = True,
                defaultValue = [0,1]
            )
        o.setMetadata({
            'widget_wrapper': {
                'useCheckBoxes': True,
                'columns': 2}})
        self.addParameter(o)

        param = QgsProcessingParameterString(name = self.FROM_DATE, description = 'Fra Dato', optional = True)
        param.setMetadata({
            'widget_wrapper': {
                'class': NullableDateTimeWrapper}})
        self.addParameter(param)
        
        param = QgsProcessingParameterString(name = self.TO_DATE, description = 'Til Dato', optional = True)
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
        
        #Filter parameters
        observation_type_indices = self.parameterAsEnums(parameters, self.OBSERVATION_TYPE, context)
        observation_types = list(map(lambda i: self.OBSERVATION_TYPES[i][0], observation_type_indices))

        from_date = None
        from_date_string = self.parameterAsString(parameters, self.FROM_DATE, context)
        if from_date_string:
            from_date = datetime.fromisoformat(from_date_string)
        feedback.setProgressText('from_date: {from_date}'.format(from_date = str(from_date)))

        to_date = None
        to_date_string = self.parameterAsString(parameters, self.TO_DATE, context)
        if to_date_string:
            to_date = datetime.fromisoformat(to_date_string)
        feedback.setProgressText('to_date: {to_date}'.format(to_date = str(to_date)))

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
            if feedback.isCanceled():
                return {}
            wkt = feature.geometry().asWkt().upper()
            geometry = Geometry(wkt)
            observations = fireDb.hent_observationer_naer_geometri(geometri=geometry, afstand=0, tidfra=from_date, tidtil=to_date)
            feedback.setProgressText('Fandt {antal} observationer'.format(antal = len(observations)))
            points = self.get_points_from_observations(fireDb, observations)
            feedback.setProgressText('Fandt {antal} punkter'.format(antal = len(points)))
            for current, observation in enumerate(observations):
                if feedback.isCanceled():
                    return {}
                observation_type_id = observation.observationstypeid
                if observation_type_id in observation_types:
                    feature = self.create_feature_from_observation(observation, points, feedback)
                    if feature: 
                        sink.addFeature(feature, QgsFeatureSink.FastInsert)
                        feedback.setProgressText('En observation blev oprettet for id =  {id}'.format(id = observation.objectid))
                    else:
                        feedback.setProgressText('En observation blev IKKE oprettet for id =  {id}'.format(id = observation.objectid))
                else:
                    feedback.setProgressText('En observation blev IKKE oprettet for id =  {id} (type ikke i kriterier)'.format(id = observation.objectid))
                    
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
    
    def canExecute(self):
        if FireDb is None:
            return False, "Dette plugin er afhængigt af API'et til Fikspunktregistret. Se venligst https://github.com/Septima/fire-qgis#installation"
        fire_connection_string = self.settings.value('fire_connection_string')
        if fire_connection_string is None:
            conf_message = 'Kan ikke finde konfigurationsfil. Se venligst https://github.com/Kortforsyningen/fire-cli#konfigurationsfil for format og placering af konfigurationsfil'
            return False, conf_message
        else:
            try:
                fireDb = FireDb(fire_connection_string)
                fireDb.hent_observationtyper()
                return True, 'OK'
            except:
                return False, 'Fejl i forbindelse til Fikspunktregistret. Se venligst https://github.com/Kortforsyningen/fire-cli#konfigurationsfil for format og indhold af konfigurationsfil'
    
    def shortHelpString(self):
        help_string = 'Importerer observationer fra Fikstpunktregistret, hvor\n- enten p1 eller p2 er indeholdt i forespørgselsgeometrien,\n- observationstype er som ønsket og\n- registrering-fra ligger indenfor dato-interval (Optionelt)\n\n'
        conf_message = ''
        fire_connection_string = self.settings.value('fire_connection_string')
        if fire_connection_string is None:
            conf_message = "Fejl i konfigurationsfil eller kan ikke finde konfigurationsfil. Se venligst https://github.com/Kortforsyningen/fire-cli#konfigurationsfil"
        else:
            fire_connection_file_path = self.settings.value('fire_connection_file_path')
            conf_message = "Konfigurationsfil: " + fire_connection_file_path
        return self.tr(help_string + conf_message)

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'ui','fire-export.png')
        return QIcon (icon_path)
