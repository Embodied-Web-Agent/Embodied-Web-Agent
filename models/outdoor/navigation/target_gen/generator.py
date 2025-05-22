from tasks.navigation.target_gen.google_maps import GoogleMaps, GeoCodingResult
from tasks.navigation.target_gen.llm import LlmPrompts, ChatBot, OpenAIChatBot
from tasks.navigation.target_gen.utils import SceneBounds, Geographic, Scene, SpotInstruction, SpotInstructionList
import json
import random

from tqdm import tqdm
from typing import Iterable

class DataCollectionPlanner:
    '''
    Collect districts with distinct features in arbitary cities,
    and organize the data collection plan
    '''
    def __init__(self, **kwargs):
        self.gmaps = GoogleMaps(**kwargs)
        self.chatbot = ChatBot(id='city recommender', model='gpt-4-turbo-preview')
        self.spot_counter = 0
        self.scene_counter = 0
        self.init_chatbot()

    def init_chatbot(self):
        self.chatbot.add_prompt(LlmPrompts.city_recommendation_prompt)

    def plan_spots(self, num=1, restriction=None) -> Iterable[GeoCodingResult]:
        '''
        Given a restriction, plan spots for data collection 
        '''
        if restriction:
            self.chatbot.add_message(f'Given the restriction {restriction}, recommend {num} places')
        else:
            self.chatbot.add_message(f'Recommend {num} places')
        
        response = self.chatbot.send()
        # print(response)
        for place in response.split('|'):
            spot = self.gmaps.get_geocode(place.strip())
            yield spot

    def plan_scenes(self, spot: GeoCodingResult, radius=10, size=(1000, 1000), margin=(-5, -5)) -> Iterable[Scene]:
        '''
        Given a spot, plan scenes for data collection
        '''
        self.spot_counter += 1
        self.scene_counter = 0
        base_lat, base_lon = spot.center
        block_offset_lat, block_offset_lon = Geographic.offset_convert(size[0] + margin[0], size[1] + margin[1], base_lat)
        for i in range(-radius+1, radius):
            for j in range(-radius+1, radius):
                center_lat = base_lat + i * block_offset_lat
                center_lon = base_lon + j * block_offset_lon
                offset_lat, offset_lon = Geographic.offset_convert(size[0] / 2, size[1] / 2, center_lat)
                bounds = SceneBounds(
                    n=center_lat + offset_lat, s=center_lat - offset_lat,
                    e=center_lon + offset_lon, w=center_lon - offset_lon
                )
                self.scene_counter += 1
                yield Scene(
                    id = f'spot_{self.spot_counter:04d}_scene_{self.scene_counter:06d}',
                    meta = {'geocode': spot.query, 'name': spot.name, 'types': spot.types, 'bounds': bounds}
                )


# Generate data from the chatbot's response
# Possible models: gpt-4o-2024-08-06, gpt-4o-mini-2024-07-18
class DataGenerator:
    def __init__(self, instruction_file, **kwargs):
        self.gmaps = GoogleMaps(**kwargs)
        self.chatbot = OpenAIChatBot(id='spot and question generator', model='gpt-4o-mini-2024-07-18', max_tokens=8192, temperature=1.0)
        self.chatbot.load_prompt_and_instruction(instruction_file)

    def generate_data(self, output_file: str = "", is_dump: bool = False):
        gdata, token_usage = self.chatbot.send(response_format=SpotInstructionList) # ignore token usage output
        output_data = []

        for gdata in gdata.spots:
            geocode_spot = self.gmaps.get_geocode(gdata.location)
            output_data.append({
                'coordinate': geocode_spot.center,
                'geocode_name': geocode_spot.name,
                'geocode_types': geocode_spot.types,
                'generated_name': gdata.location,
                'generated_instruction': gdata.instruction
            })

        random_int = random.randint(0, len(output_data) - 1) # added by rui

        if is_dump:
            with open(output_file, 'w') as f:
                json.dump(output_data[random_int], f, indent=4)
        return output_data[random_int], token_usage
    
if __name__ == '__main__':
    # planner = DataCollectionPlanner()
    # scenes = []
    # for _ in tqdm(range(10)):
    #     for spot in tqdm(planner.plan_spots(10), leave=False):
    #         for scene in tqdm(planner.plan_scenes(spot, radius=10, size=(1000, 1000), margin=(-10, -10)), leave=False):
    #             scenes.append(scene)
    
    # with open('./workspace/scenes.json', 'w') as f:
    #     json.dump(scenes, f, default=lambda x: x.__dict__, indent=4)
    
    generator = DataGenerator('./tasks/navigation/target_gen/configs/spot_and_question_gen_rui.json') # embodied/tasks/navigation/target_gen/configs
    generated_data = generator.generate_data('./tasks/navigation/target_gen/workspace/spot_test_data_4o_single_must_nyc_mini_rui_temp.json', is_dump=True)
    # generator.generate_data('./tasks/navigation/target_gen/workspace/spot_{}.json')