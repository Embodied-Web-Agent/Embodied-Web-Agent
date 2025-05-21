from dotenv import load_dotenv
import os

from utils import get_pano_meta_from_id

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


'''Class for standpoint nodes (intial and adjacent)'''
class StandpointNode:
    def __init__(self, id, latitude, longitude, parent=None):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.adjacent = []
        self.parent = parent
        self.visited = False
        self.num_adjacent = None
    
    def get_coords(self):
        return f'{self.latitude}, {self.longitude}'
    
    # Get all adjacent standpoints (degree=1)
    def store_adjacent(self, meta, session_token):
        links = meta.get('links', [])
        
        for link in links:
            pano_meta = get_pano_meta_from_id(link['panoId'], GOOGLE_API_KEY, session_token=session_token)

            if pano_meta is None:
                # print(f"No metadata found for adjacent standpoint.")
                continue

            longitude = pano_meta.get('lng', None)
            latitude = pano_meta.get('lat', None)
            self.adjacent.append(StandpointNode(link['panoId'], latitude, longitude, parent=self))

        self.num_adjacent = len(self.adjacent)