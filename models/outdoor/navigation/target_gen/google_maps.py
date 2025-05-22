import googlemaps
import math
import os
import sys 
import tempfile

from utils import Geographic, SceneBounds

from dataclasses import dataclass

@dataclass
class GeoCodingResult:
    query: str
    response_raw: dict
    @property
    def center(self):
        return (self.response_raw['geometry']['location']['lat'], self.response_raw['geometry']['location']['lng'])
    @property
    def name(self):
        return self.response_raw['address_components'][0]['long_name']
    @property
    def types(self):
        return self.response_raw['address_components'][0]['types']

class GoogleMaps(googlemaps.Client):
    DEFAULT_SIZE = (256, 256)
    DEFAULT_ZOOM = 18
    MAX_ZOOM = 21
    
    def __init__(self, api_key=None, **kwargs):
        if not api_key:
            api_key = os.environ['GOOGLE_MAP_API_KEY']
        super().__init__(key=api_key, **kwargs)

    def get_static_map(self, path: str, bounds: SceneBounds, use_fit=True, **kwargs):
        '''
        get a static map image
        params:
            path: path to save the image
            bounds: scene bounds (s, w, n, e)
            crop_to_fit: whether to crop the image to fit the extent
        '''
        if use_fit:
            # get suitable zoom level
            ne_x, ne_y = Geographic.mercator_project(bounds.n, bounds.e)
            sw_x, sw_y = Geographic.mercator_project(bounds.s, bounds.w)
            lat_scale = (ne_y - sw_y) / math.pi
            lon_scale = (ne_x - sw_x) / math.pi / 2
            scale = max(lat_scale, lon_scale)
            zoom = int(math.floor(math.log2(1 / scale)))
            zoom = max(min(zoom, self.MAX_ZOOM), 0)
            # get suitable size
            lat_scale *= 2**zoom
            lon_scale *= 2**zoom
            size = (int(lat_scale * self.DEFAULT_SIZE[0]), int(lon_scale * self.DEFAULT_SIZE[1]))
        else:
            zoom = self.DEFAULT_ZOOM
            size = self.DEFAULT_SIZE 
            
        with open(path, 'wb') as f:
            for chunk in super().static_map(
                center=bounds.center, size=size, zoom=zoom, **kwargs
            ):
                if chunk: f.write(chunk)
        
    def get_geocode(self, query: str, **kwargs):
        return GeoCodingResult(query, super().geocode(query, **kwargs)[0])

if __name__ == '__main__':
    gmaps = GoogleMaps()
    bounds = SceneBounds(s=42.35233, w=-71.07007, n=42.35902, e=-71.05351)
    os.makedirs('./workspace', exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix='.png', dir='./workspace/', delete=False) as f:
        gmaps.get_static_map(f.name, bounds, maptype='hybrid')
        print(bounds, f.name)
