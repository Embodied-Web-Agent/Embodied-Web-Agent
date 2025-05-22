import os
import io
import gym
import json
import osmnx as ox
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from tasks.navigation.utils import get_street_view_from_api, get_heading_diff

class NaviEnvConfig:
    
    def __init__(self, task_path, max_steps=50):
        self.task_path = task_path
        self.max_steps = max_steps


class NaviMap:
    
    def __init__(self, graph):
        self.graph = graph
        self.cache_hit = 0
        self.cache_miss = 0
        self.cur_heading = 0.0
    
    def get_cache_stats(self):
        return self.cache_hit, self.cache_miss
    
    def get_coordinates(self, node_id):
        if node_id not in self.graph:
            return None
        node_meta = self.graph[node_id]
        return node_meta["lat"], node_meta["lng"]
    
    def get_max_degree(self):
        max_degree = 0
        for _, node_meta in self.graph.items():
            max_degree = max(max_degree, len(node_meta["links"]))
        return max_degree
    
    def get_shortest_path(self, source_node, target_node):

        if source_node not in self.graph or target_node not in self.graph:
            return None
        
        # using BFS to find the shortest path in interns of edge number
        visited = set()
        queue = [source_node]
        parent_map = {}

        while queue:
            cur_node = queue.pop(0)
            if cur_node == target_node:
                break
            visited.add(cur_node)
            for link_node in self.graph[cur_node]["links"]:
                if link_node not in visited:
                    queue.append(link_node)
                    parent_map[link_node] = cur_node
        
        if target_node not in parent_map:
            return None
        
        path = [target_node]
        while path[-1] != source_node:
            path.append(parent_map[path[-1]])
        
        return path[::-1]
    
    def get_observation_headings(self, node_meta):
        """ 
        Return four different ego-centric headings.
        We will return headings to the linked nodes in a clockwise (right-to-left) order relative to current ego heading.
        When the links are less than 4, we will insert the gap with default headings [0, 90, 180, 270]
        """

        default_headings = [0, 90, 180, 270]

        headings = []
        for _, link_meta in node_meta["links"].items():
            ego_heading = (link_meta["heading"] - self.cur_heading) % 360.0
            headings.append(ego_heading)
        
        # sort the headings
        headings.sort()
        
        # If the headings are less than 4, insert the gap with default headings
        # We would like the inserted default heading to be in the gap with the maximum angle difference with currently added headings
        while len(headings) < 4:
            
            max_diff = 0.0
            max_diff_head = 0
            for i in range(len(headings)):
                diff = (headings[(i+1)%len(headings)] - headings[i])%360.0
                if diff > max_diff:
                    max_diff = diff
                    max_diff_head = i
            
            max_min_diff = 0.0
            for i in range(4):
                
                if max_diff_head == len(headings) - 1:
                    is_in_gap = headings[max_diff_head] < default_headings[i] or default_headings[i] < headings[0]
                else:
                    is_in_gap = headings[max_diff_head] < default_headings[i] < headings[max_diff_head+1]
                
                if is_in_gap:
                    
                    min_diff = min(get_heading_diff(default_headings[i], headings[max_diff_head]), get_heading_diff(default_headings[i], headings[(max_diff_head+1)%len(headings)]))
                    if min_diff > max_min_diff:
                        max_min_diff = min_diff
                        max_min_diff_head = i
                         
            headings.append(default_headings[max_min_diff_head])
            headings.sort()
        
        assert len(headings) == 4, f"The number of headings should be 4, get {headings} with length {len(headings)}"
        assert headings[0] < headings[1] < headings[2] < headings[3], f"The headings should be in ascending order and not equal to each other but get {headings}"

        # Some post processing to make sure the headings are in a disrable order
        diff_0 = min(abs(headings[0]), abs(headings[0] + 360), abs(headings[0] - 360))
        diff_3 = min(abs(headings[3]), abs(headings[3] + 360), abs(headings[3] - 360))
        if diff_0 > diff_3:
            headings = [headings[3]] + headings[:3]
        
        return headings

    def get_observation(self, node_id):
        if node_id not in self.graph:
            return []
        
        node_meta = self.graph[node_id]
        lat, lng = node_meta["lat"], node_meta["lng"]

        #TODO: maybe return the street view images as a list of numpy arrays
        
        street_views = []

        headings = self.get_observation_headings(node_meta)

        # rotate headings to absolute headings
        headings = [(heading + self.cur_heading) % 360 for heading in headings]

        for heading in headings:
            location=f"{lat},{lng}"
            api_key = os.getenv("GOOGLE_API_KEY")
            street_view, is_cache = get_street_view_from_api(api_key, location, heading=heading, fov=120)
            if is_cache:
                self.cache_hit += 1
            else:
                self.cache_miss += 1
            street_views.append(street_view)
        
        return street_views
    
    def move(self, node_id, action):
        """
        Move the agent to the next node based on the instructed heading
        action: 0, 1, 2, 3 (move forward, turn right, turn back, turn left)
        """
        if node_id not in self.graph:
            return node_id
        
        node_meta = self.graph[node_id]
        headings = self.get_observation_headings(node_meta)
        for i in range(4):
            headings[i] = (headings[i] + self.cur_heading) % 360

        action_nodes = [node_id, node_id, node_id, node_id]
        for link_node, link_meta in node_meta["links"].items():
            heading = link_meta["heading"]
            min_head_diff = 3600
            for head_id, head in enumerate(headings):
                head_diff = get_heading_diff(heading, head)
                if head_diff < min_head_diff:
                    min_head_diff = head_diff
                    min_head_id = head_id
            assert min_head_diff == 0.0, f"heading should be in observation headings for linked ndoes, but get minimum head difference {min_head_diff}"
            action_nodes[min_head_id] = link_node
        
        self.cur_heading = headings[action]
        return action_nodes[action]
        

class NaviEnv(gym.Env):
    
    def __init__(self, config: NaviEnvConfig, visualize_map=False):
        self.config = config
        with open(config.task_path, "r") as f:
            task_json = json.load(f)
        self.source_node = task_json["source"]
        self.target_node = task_json["target"]
        self.map = NaviMap(task_json["graph"])
        self.viualize_map = visualize_map

        if visualize_map:
            source_lat, source_lon = self.map.get_coordinates(self.source_node)
            target_lat, target_lon = self.map.get_coordinates(self.target_node)
            distance = ox.distance.great_circle_vec(source_lat, source_lon, target_lat, target_lon)
            self.osm_graph = ox.graph_from_point((source_lat, source_lon), dist=distance * 2.5, network_type="all")
            self.osm_graph.add_node(-2, x=target_lon, y=target_lat)
            self.shortest_path = self.map.get_shortest_path(self.source_node, self.target_node)
            self.shortest_path_index = []
            assert self.shortest_path is not None, "No path found between source and target, the task is not solvable"
            assert self.map.get_max_degree() <= 4, "The map is too complex because one node has more than 4 edges, the agent may not be able to handle it"

            for i, node in enumerate(self.shortest_path[:-1]):
                lat, lon = self.map.get_coordinates(node)
                self.osm_graph.add_node(-3-i, x=lon, y=lat)
                self.shortest_path_index.append(-3-i)
                
        
        self.reset()

    def reset(self):
        self.current_location = self.source_node
        return self.map.get_observation(self.source_node)

    def step(self, action):
        next_location = self.map.move(self.current_location, action)
        info = {}
        reward = 0
        done = False
        
        if next_location == self.target_node:
        #TODO: add a distance threshold for the target node
            reward = 1
            done = True
            info = {"reason": "Target reached"}
        elif next_location == self.current_location:
            reward = -0.1
            info = {"reason": "No link in the instructed direction"}
        
        self.current_location = next_location
        info["obs_cache_hit"], info["obs_cache_miss"] = self.map.get_cache_stats()
        info["obs_cache_hit_rate"] = info["obs_cache_hit"] / (info["obs_cache_hit"] + info["obs_cache_miss"])
        
        return self.map.get_observation(self.current_location), reward, done, info
    
    def render(self, obs):

        # For human to view the observation, put the front view to the second position, left view to the first position
        obs = [obs[3]] + obs[:3]
        
        def concat_images(images):
            images = [image.resize((images[0].width, images[0].height)) for image in images]
            arrays = [np.array(image) for image in images]
            concat_array = np.concatenate(arrays, axis=1)
            # Convert numpy array back to image
            return Image.fromarray(concat_array)
        
        if self.viualize_map:
            cur_lat, cur_lon = self.map.get_coordinates(self.current_location)
            if self.osm_graph.has_node(-1):
                self.osm_graph.remove_node(-1)
            
            self.osm_graph.add_node(-1, x=cur_lon, y=cur_lat)
            node_colors = ['white' for _ in self.osm_graph.nodes()]
            for i, node in enumerate(self.osm_graph.nodes()):
                if node == -1:
                    node_colors[i] = "red" 
                elif node == -2:
                    node_colors[i] = "green"
                elif node in self.shortest_path_index:
                    node_colors[i] = 'blue'

            fig, _ = ox.plot_graph(self.osm_graph, node_color=node_colors, figsize=(6,6), show=False)

            # Convert fig to PIL image
            with io.BytesIO() as buf:
                fig.tight_layout(pad=0)
                fig.savefig(buf, format='png')
                buf.seek(0)
                img = Image.open(buf).convert('RGB')
            plt.close(fig)

            return concat_images([obs[0], obs[1], obs[2], obs[3], img])
        
        return concat_images(obs)
