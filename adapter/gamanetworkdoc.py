from typing import List, Dict
import math
from fireapi.model import Observation, Punkt
from fireapi import FireDb
from platform import dist

class GamaNetworkDoc():
    def __init__(self, fireDb: FireDb, parameters):
        #Input parametrs
        self.fireDb = fireDb
        self.parameters = parameters
        self.description_header = "Network doc created by fire-gama (https://github.com/Septima/fire-gama)"
        self.description_items = [self.description_header]
        self.observations = []
        self.fixed_points = []
        
        #Local parameters
        self.adjustable_points = []
        self.relevant_observations = []
        
    def add_description(self, description):
        self.description_items.append(description)
    
    def set_observations(self, observations: List[Observation]):
        self.observations = observations
        self.add_description("GamaNetworkDoc.set_observations: Antal observationer: " + str(len(observations)))
        
    def set_fixed_points(self, fixed_points: List[Punkt]):
        self.fixed_points = fixed_points
        self.add_description("GamaNetworkDoc.set_fixed_points: Antal punkter: " + str(len(fixed_points)))
    
    def write(self, stream, heights: bool, positions: bool):
        output = self.get_template()
        output = self.insert_network_attributes(self.parameters, output)
        output = self.insert_network_parameters(self.parameters, output)
        self.relevant_observations = self.filter_observations(self.observations, heights, positions)
        self.adjustable_points = self.get_points_from_observations(self.relevant_observations)
        output = self.insert_points_observations_attributes(self.parameters, output)
        output = self.insert_fixed_points(self.fixed_points, heights, positions, output)
        output = self.insert_adjustable_points(self.adjustable_points, heights, positions, output)
        output =self.insert_observations(self.relevant_observations, heights, positions, output)
        output = self.insert_description(self.description_items, output)
        stream.write(output)
    
    def get_template(self):
        template = '<?xml version="1.0" ?>\n' \
        '<gama-local xmlns="http://www.gnu.org/software/gama/gama-local">\n' \
        '    <network {networkAttributes}>\n' \
        '        {networkParameters}\n' \
        '        <description>\n' \
        '            {description}\n' \
        '        </description>\n' \
        '        <points-observations {points-observations-attributes}>\n' \
        '            {fixedPoints}\n' \
        '            {adjustablePoints}\n' \
        '            {obs}\n' \
        '        </points-observations>\n' \
        '    </network>\n' \
        '</gama-local>'
        return template
    
    def insert_network_attributes(self, parameters: Dict, doc):
        return str.replace(doc, "{networkAttributes}", "")
        
    def insert_network_parameters(self, parameters: Dict, doc):
        return str.replace(doc, "{networkParameters}", "")
    
    def insert_description(self, description_items: List[str], doc):
        return str.replace(doc, "{description}", '\n            '.join(description_items))
    
    def filter_observations(self, observations: List[Observation], heights: bool, positions: bool):
        filtered_observations = []
        for o in observations:
            #Filter for None in udgang or sigte (o.opstillingspunktid, o.sigtepunktid not none)
            if (o.opstillingspunktid is not None) and (o.sigtepunktid is not None):
                #Filter for suitability to establish height (o.observationstypeid in ['trigonometrisk_koteforskel', geometrisk_koteforskel])
                if o.observationstypeid in ['trigonometrisk_koteforskel', 'geometrisk_koteforskel']:
                    values = self.get_values(o, heights, positions)
                    if values is not None:
                        setattr(o, 'gama_values', values)
                        #o['gama_values'] = values
                        filtered_observations.append(o)
        #Filter for epsg? 'trigonometrisk_koteforskel': dev=math.sqrt((o.value4 + o.value5)/o.antal) / 'geometrisk_koteforskel': dev=math.sqrt((o.value4 + o.value5)/o.antal) // val=o.value1
        return filtered_observations
    
    def get_values(self, observation: Observation, heights: bool, positions: bool):
        if observation.observationstypeid == 'trigonometrisk_koteforskel':
            if (observation.value4 is not None) and (observation.value5 is not None) and (observation.antal is not None) and (observation.antal != 0):
                dev=math.sqrt((observation.value4 + observation.value5)/observation.antal)
                val=observation.value1
                if observation.value2 is not None:
                    dist = observation.value2/1000
                else: 
                    dist='?'
                return {'dev': dev, 'val': val, 'dist': dist}
        if observation.observationstypeid == 'geometrisk_koteforskel':
            if (observation.value5 is not None) and (observation.value6 is not None) and (observation.antal is not None) and (observation.antal != 0):
                dev=math.sqrt((observation.value5 + observation.value6)/observation.antal)
                val=observation.value1
                if observation.value2 is not None:
                    dist = observation.value2/1000
                else: 
                    dist='?'
                return {'dev': dev, 'val': val, 'dist': dist}
        return None
    
    def get_points_from_observations(self, observations: List[Observation]):
        point_ids_dict = {}
        points_list = []
        for o in observations:
            op_id = o.opstillingspunktid
            if op_id not in point_ids_dict:
                op = self.fireDb.hent_punkt(op_id)
                point_ids_dict[op_id] = op
                points_list.append(op)
        return points_list
    
    def insert_points_observations_attributes(self, parameters: Dict, doc):
        return str.replace(doc, "{points-observations-attributes}", "")
    
    def insert_fixed_points(self, points: List[Punkt], heights: bool, positions: bool, doc):
        fixed_points = []
        for fixed_point in points:
            fixed_points.append(self.get_fixed_height_point_element(fixed_point))
        return str.replace(doc, "{fixedPoints}", '\n            '.join(fixed_points))
        
    def insert_adjustable_points(self, points: List[Punkt], heights: bool, positions: bool, doc):
        adjustable_points = []
        for adjustable_point in points:
            adjustable_points.append(self.get_adjustable_height_point_element(adjustable_point))
        return str.replace(doc, "{adjustablePoints}", '\n            '.join(adjustable_points))
    
    def insert_observations(self, observations: List[Observation], heights: bool, positions: bool, doc):
        observation_elements = []
        for o in observations:
            observation_elements.append(self.get_dh_element(o))
        return str.replace(doc, "{obs}", '\n            '.join(observation_elements))
    
    def get_height_differences_template(self):
        template = '<height-differences>' \
        '    [dhs]' \
        '</height-differences>'
        return template
    
    def get_fixed_height_point_element(self, point: Punkt):
        return '<point id="{id}" z="zzz.zzz" fix="z" />'.format(id= point.id)
    
    def get_adjustable_height_point_element(self, point: Punkt):
        return '<point id="{id}" adj="z" />'.format(id= point.id)

    def get_dh_element(self, observation: Observation):
        fromId= observation.opstillingspunktid
        toId=observation.sigtepunktid
        gamavalues = getattr(observation, 'gama_values')
        val=gamavalues['val']
        dist=gamavalues['dist']
        dev=gamavalues['dev']
        return '<dh from="{fromId}" to="{toId}" val="{val}" dist="{dist}" stdev="{dev}" />'.format(fromId = fromId, toId=toId, val=val, dist=dist, dev=dev)

