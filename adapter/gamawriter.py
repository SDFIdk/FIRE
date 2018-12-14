from typing import List
from fireapi import FireDb
from fireapi.model import Punkt
from .gamanetworkdoc import GamaNetworkDoc

class GamaWriter(object):
    def __init__(self, fireDb: FireDb, output_stream):
        #Input parametrs
        self.fireDb = fireDb
        self.output_stream = output_stream
        self.fixed_points = []
        
        #Local parameters
        self.obsList = []
        
    def set_fixed_points(self, fixed_points: List[Punkt]):
        self.fixed_points = fixed_points
        
    def take_all_points(self):
        points = self.fireDb.hent_alle_punkter()
        #id='3840df67-94aa-49ca-84fb-ea9e808b44d1', objectid=2, sagseventid='3840df67-94aa-49ca-84fb-ea9e808b44d1'
        obsDict = {}
        for point in points:
            of = point.observationer_fra
            for o in of:
                if o.objectid not in obsDict:
                    obsDict[o.objectid] = o
                    self.obsList.append(o)
            ot = point.observationer_til
            for o in ot:
                if o.objectid not in obsDict:
                    obsDict[o.objectid] = o
                    self.obsList.append(o)
            
        self.point_set_description = "GamaWriter.take_all_points() Antal punkter: " + str(len(points))
        
    def write(self, heights, pos, parent_description, parameters):
        self.parent_description = parent_description
        
        doc = GamaNetworkDoc( self.fireDb, parameters)
        doc.add_description(parent_description + " -> " + self.point_set_description)
        doc.set_fixed_points(self.fixed_points)
        doc.set_observations(self.obsList)
        doc.write(self.output_stream, heights, pos)
    
    