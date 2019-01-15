import ast
import xml.etree.ElementTree as ET

from fireapi import FireDb
from fireapi.model import Beregning, Koordinat, Sagsevent

class GamaReader(object):
    def __init__(self, fireDb: FireDb, input_stream):
        #Input parametrs
        self.fireDb = fireDb
        self.input_stream = input_stream
        
    def read(self, sags_id):

        sag = self.fireDb.hent_sag(sags_id)

        namespace = "{http://www.gnu.org/software/gama/gama-local-adjustment}"
        tree = ET.parse(self.input_stream)
        root = tree.getroot()
        
        description_element = root.find(namespace + "description")
        description = description_element.text
        
        observation_ids_start = description.find("{observation_ids}") + len("{observation_ids} :")
        observation_ids_end = description.find("{/observation_ids}")
        observation_ids = description[observation_ids_start:observation_ids_end]
        observation_id_list= ast.literal_eval(observation_ids)
        observation_list = self.fireDb.hent_observationer(observation_id_list)

        beregning = Beregning() 
        beregning.observationer.extend(observation_list)
        
        srid = self.fireDb.hent_srid('DK:DVR90')
        
        adjusted_element = root.find(namespace + "coordinates").find(namespace + "adjusted")
        for point in adjusted_element.iter(namespace + "point"):
            z = point.find(namespace + "z").text
            punktid = point.find(namespace + "id").text
            koordinat = Koordinat()
            koordinat.srid = srid
            koordinat.z = z
            koordinat.transformeret = "false"
            p = self.fireDb.hent_punkt(punktid)
            koordinat.punkt = p
            beregning.koordinater.append(koordinat)
    
        self.fireDb.indset_beregning(Sagsevent(sag=sag), beregning)
