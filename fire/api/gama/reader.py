import math
import xml.etree.ElementTree as ET

from fire.api import FireDb
from fire.api.model import Beregning, Koordinat, Sagsevent, SagseventInfo, EventType


class GamaReader(object):
    def __init__(self, fireDb: FireDb, input_stream):
        # Input parametrs
        self.fireDb = fireDb
        self.input_stream = input_stream

    def read(self, sags_id):
        sag = self.fireDb.hent_sag(sags_id)

        namespace = "{http://www.gnu.org/software/gama/gama-local-adjustment}"
        tree = ET.parse(self.input_stream)
        root = tree.getroot()

        beregning = Beregning()

        srid = self.fireDb.hent_srid("EPSG:5799")

        adjusted_element = root.find(namespace + "coordinates").find(
            namespace + "adjusted"
        )
        cov_mat_values = (
            root.find(namespace + "coordinates")
            .find(namespace + "cov-mat")
            .findall(namespace + "flt")
        )
        original_index_indicies = (
            root.find(namespace + "coordinates")
            .find(namespace + "original-index")
            .findall(namespace + "ind")
        )

        for idx, point in enumerate(adjusted_element.iter(namespace + "point")):
            # Read values from the point
            z = point.find(namespace + "z").text
            point_id = point.find(namespace + "id").text

            # Read the correct entry in cov_mat_values
            cov_mat_index = int(original_index_indicies[idx].text) - 1
            cov_mat_element = cov_mat_values[cov_mat_index]
            # Read value as float
            cov_mat_value = float(cov_mat_element.text)
            # .. and tale sqrt to find std_dev
            std_dev = math.sqrt(cov_mat_value)

            koordinat = Koordinat()
            koordinat.srid = srid
            koordinat.z = z
            koordinat.sz = std_dev
            koordinat.punkt = self.fireDb.hent_punkt(point_id)
            beregning.koordinater.append(koordinat)

        observation_id_list = []
        observations_element = root.find(namespace + "observations")
        for idx, diff in enumerate(
            observations_element.iter(namespace + "height-diff")
        ):
            observationId = diff.get("extern")
            observation_id_list.append(observationId)

        observation_list = self.fireDb.hent_observationer(observation_id_list)
        beregning.observationer.extend(observation_list)

        self.fireDb.indset_sagsevent(
            Sagsevent(
                sag=sag,
                eventtype=EventType.KOORDINAT_BEREGNET,
                sagseventinfos=[
                    SagseventInfo(beskrivelse="Beregning indlæst via GNU Gama")
                ],
                beregninger=[beregning],
                koordinater=beregning.koordinater,
            )
        )
