# -*- coding: utf-8 -*-
from fire.api.model.punkttyper import GeometriObjekt, PunktInformation

__author__ = "Septima"
__date__ = "2019-12-02"
__copyright__ = "(C) 2019 by Septima"

import os
from datetime import datetime

from typing import List, Dict

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon
from qgis.core import (
    QgsProcessing,
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
    QgsPoint,
    QgsProject,
)

from qgis.PyQt.QtCore import Qt, QVariant, QDateTime, QTime

try:
    from fire.api import FireDb
except:
    FireDb = None

from fire.api.model import Geometry, Observation, Punkt, Koordinat
from .datetime_widget import DateTimeWidget
from .ui.nullable_datetime_wrapper import NullableDateTimeWrapper

import processing


class ImportObservationerByLocationAlgorithm(QgsProcessingAlgorithm):

    OUTPUT = "OUTPUT"
    INPUT = "INPUT"
    OBSERVATION_TYPE = "OBSERVATION_TYPE"
    APPLY_THEME = "APPLY_THEME"
    FROM_DATE = "FROM_DATE"
    TO_DATE = "TO_DATE"

    def __init__(self, settings):
        QgsProcessingAlgorithm.__init__(self)
        self.settings = settings

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Importér observationer indenfor (within)"),
                [QgsProcessing.TypeVectorPolygon],
            )
        )

        self.OBSERVATION_TYPES = [
            (1, self.tr("Koteforskel opmålt geometrisk")),
            (2, self.tr("Koteforskel opmålt trigonometrisk")),
        ]

        o = QgsProcessingParameterEnum(
            name=self.OBSERVATION_TYPE,
            description=self.tr("Observationstype"),
            options=[x[1] for x in self.OBSERVATION_TYPES],
            allowMultiple=True,
            defaultValue=[0, 1],
        )
        o.setMetadata({"widget_wrapper": {"useCheckBoxes": True, "columns": 2}})
        self.addParameter(o)

        param = QgsProcessingParameterString(
            name=self.FROM_DATE, description="Fra Dato", optional=True
        )
        param.setMetadata({"widget_wrapper": {"class": NullableDateTimeWrapper}})
        self.addParameter(param)

        param = QgsProcessingParameterString(
            name=self.TO_DATE, description="Til Dato", optional=True
        )
        param.setMetadata({"widget_wrapper": {"class": NullableDateTimeWrapper}})
        self.addParameter(param)

        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr("Observationer"))
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.APPLY_THEME,
                self.tr("Anvend standard fikspunktregister-symbologi"),
                defaultValue=True,
            )
        )

    def processAlgorithm(self, parameters, context, feedback: QgsProcessingFeedback):
        # Input / Output
        source = self.parameterAsSource(parameters, self.INPUT, context)
        (sink, dest_id) = self.create_output_sink(
            parameters, context, source.sourceCrs()
        )

        # Filter parameters
        observation_type_indices = self.parameterAsEnums(
            parameters, self.OBSERVATION_TYPE, context
        )
        observation_types = list(
            map(lambda i: self.OBSERVATION_TYPES[i][0], observation_type_indices)
        )

        from_date = None
        from_date_string = self.parameterAsString(parameters, self.FROM_DATE, context)
        if from_date_string:
            from_date = datetime.fromisoformat(from_date_string)

        to_date = None
        to_date_string = self.parameterAsString(parameters, self.TO_DATE, context)
        if to_date_string:
            to_date = datetime.fromisoformat(to_date_string)

        fire_connection_string = self.settings.value("fire_connection_string")
        fireDb = FireDb(fire_connection_string, debug=True)

        features = list(source.getFeatures())
        total_num_features = len(features)
        total_num_features_processed = 0
        # for current, feature in enumerate(features):
        for feature in features:
            if feedback.isCanceled():
                return {}
            wkt = feature.geometry().asWkt().upper()
            geometry = Geometry(wkt)
            observations = fireDb.hent_observationer_naer_geometri(
                geometri=geometry, afstand=0, tidfra=from_date, tidtil=to_date
            )

            pid_list = self.get_pids_from_observations(observations)
            geometriobjekter = self.get_geometriobjekter_from_pids(fireDb, pid_list)
            idents = self.get_idents_from_pids(fireDb, pid_list)

            feedback.setProgressText(
                "Fandt {antal} observationer".format(antal=len(observations))
            )
            feedback.setProgressText(
                "Fandt {antal} geometriobjekter".format(antal=len(geometriobjekter))
            )
            feedback.setProgressText("Fandt {antal} idents".format(antal=len(idents)))
            for current, observation in enumerate(observations):
                observation_type_id = observation.observationstypeid
                if observation_type_id in observation_types:
                    feature = self.create_feature_from_observation(
                        observation, geometriobjekter, idents, feedback
                    )
                    if feature:
                        sink.addFeature(feature, QgsFeatureSink.FastInsert)
            total_num_features_processed = total_num_features_processed + 1
            feedback.setProgress(total_num_features_processed / total_num_features)
            if feedback.isCanceled():
                return {}

        apply_theme = self.parameterAsBool(parameters, self.APPLY_THEME, context)
        if apply_theme:
            style_file = os.path.join(
                os.path.dirname(__file__), "..", "styles", "observation.qml"
            )
            alg_params = {"INPUT": dest_id, "STYLE": style_file}
            processing.run(
                "qgis:setstyleforvectorlayer",
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )

        return {self.OUTPUT: dest_id}

    def create_output_sink(self, parameters, context, crs):
        fields = QgsFields()
        fields.append(QgsField("observation_id", QVariant.String))
        fields.append(QgsField("observation_type_id", QVariant.Double))
        fields.append(QgsField("fikspunkt1_uuid", QVariant.String))
        fields.append(QgsField("fikspunkt1_ident", QVariant.String))
        fields.append(QgsField("fikspunkt2_uuid", QVariant.String))
        fields.append(QgsField("fikspunkt2_ident", QVariant.String))
        fields.append(QgsField("registrering_fra", QVariant.DateTime))
        fields.append(QgsField("registrering_fra_iso", QVariant.String))
        fields.append(QgsField("koteforskel", QVariant.Double))
        fields.append(QgsField("nivellementslaengde", QVariant.Double))
        fields.append(QgsField("antal_opstillinger", QVariant.Double))
        fields.append(QgsField("afstandsafhaengig_varians", QVariant.Double))
        fields.append(QgsField("afstandsuafhaengig_varians", QVariant.Double))
        fields.append(QgsField("Praecisionsnivellement", QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context, fields, QgsWkbTypes.LineString, crs
        )

        return (sink, dest_id)

    def get_pids_from_observations(self, observations: List[Observation]):
        pid_list = []
        for o in observations:
            op_id = o.opstillingspunktid
            if op_id not in pid_list:  # Point not already found
                pid_list.append(op_id)
            sp_id = o.sigtepunktid
            if sp_id not in pid_list:  # Point not already found
                pid_list.append(sp_id)
        return pid_list

    def get_geometriobjekter_from_pids(self, fireDb, pid_list):
        # return dict of {punktid: geometriobjekt}

        # Get geometriobjekter
        gos: List[GeometriObjekt] = fireDb.session.query(GeometriObjekt).filter(
            GeometriObjekt.punktid.in_(pid_list),
            GeometriObjekt._registreringtil == None,
        ).all()
        go_by_pid = {}
        for go in gos:
            go_by_pid[go.punktid] = go
        return go_by_pid

    def get_idents_from_pids(self, fireDb, pid_list):
        # return dict of {punktid: ident: string}

        # GI(346)->GNSS(343)->landsnr(342)->refgeo_id(344)->uuid
        info_type_list = [346, 343, 342, 344]
        infos: List[PunktInformation] = fireDb.session.query(PunktInformation).filter(
            PunktInformation.punktid.in_(pid_list),
            PunktInformation.infotypeid.in_(info_type_list),
        ).order_by(PunktInformation.punktid, PunktInformation.infotypeid).all()

        ident_by_pid = {}
        if len(infos) > 0:
            current_index = 0
            while current_index is not None:
                current_info: PunktInformation = infos[current_index]
                current_pid = current_info.punktid
                ident = self.get_index_ident(current_index, infos)
                ident_by_pid[current_pid] = ident
                current_index = self.next_index(current_index, infos)
        return ident_by_pid

    def get_index_ident(self, current_index, infos: List[PunktInformation]):
        current_pid = infos[current_index].punktid
        best_info = infos[current_index]
        best_info_weight = self.get_info_weight(best_info)
        inc = 1
        while (
            current_index + inc < len(infos)
            and infos[current_index + inc].punktid == current_pid
        ):
            current_info = infos[current_index + inc]
            current_info_weight = self.get_info_weight(current_info)
            if current_info_weight > best_info_weight:
                best_info = current_info
                best_info_weight = current_info_weight
            inc = inc + 1
        return self.get_ident_text(best_info)

    def get_info_weight(self, info: PunktInformation):
        if info.infotypeid == 346:
            return 4
        elif info.infotypeid == 343:
            return 3
        elif info.infotypeid == 342:
            return 2
        elif info.infotypeid == 344:
            return 1

    def get_ident_text(self, info: PunktInformation):
        if info.infotypeid == 346:
            return "GI:" + info.tekst
        elif info.infotypeid == 343:
            return "GNSS:" + info.tekst
        elif info.infotypeid == 342:
            return "landsnr:" + info.tekst
        elif info.infotypeid == 344:
            return "refgeo_id:" + info.tekst

    def next_index(self, current_index, infos: List[PunktInformation]):
        current_pid = infos[current_index].punktid
        inc = 1
        while (
            current_index + inc < len(infos)
            and infos[current_index + inc].punktid == current_pid
        ):
            inc = inc + 1
        if current_index + inc < len(infos):
            return current_index + inc
        else:
            return None

    def create_feature_from_observation(
        self,
        observation: Observation,
        geometriobjekter: Dict[str, GeometriObjekt],
        idents: Dict[str, str],
        feedback: QgsProcessingFeedback,
    ):
        observation_id = observation.objectid

        fikspunkt1_id = observation.opstillingspunktid
        fikspunkt1_ident = "uuid:" + fikspunkt1_id
        if fikspunkt1_id in idents:
            fikspunkt1_ident = idents[fikspunkt1_id]

        fikspunkt2_id = observation.sigtepunktid
        fikspunkt2_ident = "uuid:" + fikspunkt2_id
        if fikspunkt2_id in idents:
            fikspunkt2_ident = idents[fikspunkt2_id]

        geometriobjekt1 = geometriobjekter[fikspunkt1_id]
        geometriobjekt2 = geometriobjekter[fikspunkt2_id]
        line_geometry = self.create_line_geometry_from_geometriobjekter(
            geometriobjekt1, geometriobjekt2, feedback
        )

        if line_geometry:
            # create the feature
            fet = QgsFeature()
            fet.setGeometry(line_geometry)
            # Felter, der skal gemmes på feature:
            #    [QgsField("observation_id", QVariant.String),
            #     QgsField("observation_type_id", QVariant.Double)
            #     QgsField("fikspunkt1_id", QVariant.String),
            #     QgsField("fikspunkt1_ident", QVariant.String),
            #     QgsField("fikspunkt2_id", QVariant.String),
            #     QgsField("fikspunkt2_ident", QVariant.String),
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
                afstandsafhaengig_varians = observation.value5
                afstandsuafhaengig_varians = observation.value6
                Praecisionsnivellement = observation.value7
            elif observation_type_id == 2:
                afstandsafhaengig_varians = observation.value4
                afstandsuafhaengig_varians = observation.value5
                Praecisionsnivellement = 0
            else:
                # Observationstypeid > 2
                feedback.setProgressText(
                    "observation_type_id > 2 for observation med id =  {id}. Springes over".format(
                        id=observation_id
                    )
                )
                return None

            # create the feature
            feature = QgsFeature()
            feature.setGeometry(line_geometry)
            feature.setAttributes(
                [
                    observation_id,
                    observation_type_id,
                    fikspunkt1_id,
                    fikspunkt1_ident,
                    fikspunkt2_id,
                    fikspunkt2_ident,
                    registrering_fra,
                    registrering_fra_iso,
                    koteforskel,
                    nivellementslaengde,
                    antal_opstillinger,
                    afstandsafhaengig_varians,
                    afstandsuafhaengig_varians,
                    Praecisionsnivellement,
                ]
            )

            return feature
        else:
            # A geometry could not be established
            feedback.setProgressText(
                "En liniegeometri kunne IKKE opettes for observation med id =  {id}".format(
                    id=observation_id
                )
            )
            return None

    def create_line_geometry_from_geometriobjekter(
        self,
        geometriobjekt1: GeometriObjekt,
        geometriobjekt2: GeometriObjekt,
        feedback: QgsProcessingFeedback,
    ):
        if geometriobjekt1 and geometriobjekt2:
            wkt1 = geometriobjekt1.geometri.wkt
            g1 = QgsPoint()
            g1.fromWkt(wkt1)
            wkt2 = geometriobjekt2.geometri.wkt
            g2 = QgsPoint()
            g2.fromWkt(wkt2)
            geom = QgsGeometry.fromPolyline([g1, g2])
            return geom
        else:
            return None

    def name(self):
        return "fire-import-observations-location"

    def displayName(self):
        return "Importér observationer fra FIRE ud fra placering"

    def group(self):
        return ""

    def groupId(self):
        return ""

    def flags(self):
        return QgsProcessingAlgorithm.FlagNoThreading

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return ImportObservationerByLocationAlgorithm(self.settings)

    def canExecute(self):
        if FireDb is None:
            return (
                False,
                "Dette plugin er afhængigt af API'et til Fikspunktregistret. Se venligst https://github.com/Septima/fire-qgis#installation",
            )
        fire_connection_string = self.settings.value("fire_connection_string")
        if fire_connection_string is None:
            conf_message = "Kan ikke finde konfigurationsfil. Se venligst https://github.com/Kortforsyningen/fire-cli#konfigurationsfil for format og placering af konfigurationsfil"
            return False, conf_message
        else:
            try:
                fireDb = FireDb(fire_connection_string)
                fireDb.hent_observationtyper()
                return True, "OK"
            except Exception as ex:
                str_ex = str(ex)
                fire_connection_file_path = self.settings.value(
                    "fire_connection_file_path"
                )
                return (
                    False,
                    "Fejl i forbindelse til Fikspunktregistret. Se venligst https://github.com/Kortforsyningen/fire-cli#konfigurationsfil for format og indhold af konfigurationsfil.          Exception:["
                    + str_ex
                    + "]  Konfigurationsfil:["
                    + fire_connection_file_path
                    + "]",
                )

    def shortHelpString(self):
        help_string = "Importerer observationer fra Fikstpunktregistret, hvor\n- enten p1 eller p2 er indeholdt i forespørgselsgeometrien,\n- observationstype er som ønsket og\n- registrering-fra ligger indenfor dato-interval (Optionelt)\n\n"
        conf_message = ""
        fire_connection_string = self.settings.value("fire_connection_string")
        if fire_connection_string is None:
            conf_message = "Fejl i konfigurationsfil eller kan ikke finde konfigurationsfil. Se venligst https://github.com/Kortforsyningen/fire-cli#konfigurationsfil"
        else:
            fire_connection_file_path = self.settings.value("fire_connection_file_path")
            conf_message = "Konfigurationsfil: " + fire_connection_file_path
        return self.tr(help_string + conf_message)

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "ui", "fire-export.png")
        return QIcon(icon_path)
