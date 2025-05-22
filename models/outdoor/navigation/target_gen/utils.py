import math
from dataclasses import dataclass, field
from pydantic import BaseModel
from typing import List

class SpotInstruction(BaseModel):
    location: str
    instruction: str

class SpotInstructionList(BaseModel):
    spots: List[SpotInstruction]

@dataclass
class Scene:
    id: str = ''
    meta: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict)

@dataclass
class SceneBounds:
    s: float
    w: float
    n: float
    e: float
    @property
    def center(self):
        return ((self.n + self.s) / 2, (self.w + self.e) / 2)
    @property
    def ne(self):
        return (self.n, self.e)
    @ne.setter
    def ne(self, value):
        self.n, self.e = value
    @property
    def sw(self):
        return (self.s, self.w)
    @sw.setter
    def sw(self, value):
        self.s, self.w = value
    @property
    def is_valid(self):
        return -90 <= self.s < self.n <= 90 and -180 <= self.w <= 180 and -180 <= self.e <= 180
    @property
    def is_trival(self):
        # do not cross the 180E/W longitude, and do not clipped by mercator projection
        return self.w < self.e and -85.0511 <= self.s < self.n <= 85.0511

class Geographic:
    pole_circumference = 40_007_863 # (m)
    equator_circumference = 40_075_017 # (m)
    radius = 6_371_000 # (m)

    @staticmethod
    def mercator_project(lat=0., lon=0., clip=True):
        '''
        see: https://mathworld.wolfram.com/MercatorProjection.html
        '''
        x = math.radians(lon)
        y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
        if clip:
            # lat should be witin 85.0511S and 85.0511N
            y = min(max(y, -math.pi), math.pi)
            x = min(max(x, -math.pi), math.pi)
        return x, y

    @staticmethod
    def inverse_mercator_project(x=0., y=0., clip=True):
        '''
        see: https://mathworld.wolfram.com/MercatorProjection.html
        '''
        lon = math.degrees(x)
        lat = math.degrees(2 * math.atan(math.exp(y)) - math.pi / 2)
        if clip:
            lon = min(max(lon, -180), 180)
            lat = min(max(lat, -90), 90)
        return lat, lon

    @staticmethod
    def offset_convert(ns_offset=0., ew_offset=0., base_lat=0.):
        '''
        Given a base latitude, convert ns/ew offset (in meters) to lat/lon offset (in degrees)
        '''
        lat_offset = ns_offset / Geographic.pole_circumference * 360
        lon_offset = ew_offset / (Geographic.equator_circumference * math.cos(math.radians(base_lat))) * 360
        return lat_offset, lon_offset

    @staticmethod
    def distance(lat1, lon1, lat2, lon2):
        '''
        Calculate the distance between two points on the Earth
        '''
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return c * Geographic.radius
