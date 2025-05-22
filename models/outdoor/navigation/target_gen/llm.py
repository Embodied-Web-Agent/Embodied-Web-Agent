import openai 
import requests
import base64
import os
import json
import io

from PIL import Image
from dataclasses import dataclass

# prompt
from tasks.navigation.data_collection.prompt.web_task_gen_rui import SUB_TASK_GEN_PROMPT, SUB_TASK_SYSTEM_PROMPT

class ChatBot:
    api_url = 'https://api.openai.com/v1/chat/completions'

    def __init__(self, id='', model='gpt-4-vision-preview', api_key=None, max_tokens=150, temperature=0.7, top_p=1.0, *kwargs):
        self.id = id
        if not api_key:
            api_key = os.environ['OPENAI_API_KEY']
        self.api_key = api_key
        self.payload = {
            'model': model,
            'messages': [],
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p,
        }

    @property
    def model(self):
        return self.payload['model']

    @model.setter
    def model(self, value):
        self.payload['model'] = value

    @property
    def max_tokens(self):
        return self.payload['max_tokens']

    @max_tokens.setter
    def max_tokens(self, value):
        self.payload['max_tokens'] = value

    @property
    def messages(self):
        return self.payload['messages']
    
    def add_prompt(self, prompt):
        self.payload['messages'].append({'role': 'system', 'content': prompt})

    def add_message(self, message, message_type='text'):
        buffer = self.messages[-1]
        if buffer['role'] != 'user':
            self.messages.append({'role': 'user', 'content': []})
            buffer = self.messages[-1] 
        if message_type == 'text':
            buffer['content'].append({'type': 'text', 'text': message})
        elif message_type == 'image_url':
            buffer['content'].append({'type': 'image_url', 'image_url': {'url': ChatBot.encode_image(message)}})
        else:
            raise ValueError(f'Invalid message type: {message_type}')

    def parse_response(self, response):
        content = response['choices'][0]['message']['content']
        self.messages.append({'role': 'assistant', 'content': content})
        return content

    def send(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }
        response = requests.post(
            self.api_url,
            headers=headers,
            data=json.dumps(self.payload),
            timeout=300,
        )
        response.raise_for_status()
        return self.parse_response(response.json())

    @staticmethod
    def encode_image(image_path, max_height=128):
        image_path = os.path.realpath(image_path)
        extension = os.path.splitext(image_path)[1][1:]

        image = Image.open(image_path)
        if image.height > max_height:
            image = image.resize((image.width * max_height // image.height, max_height))
        
        byte_stream = io.BytesIO()
        image.save(byte_stream, format=extension.upper())
        byte_stream.seek(0)
        
        code = base64.b64encode(byte_stream.read()).decode('utf-8')
        return f'data:image/{extension};base64,{code}'

@dataclass
class LlmPrompts:
    text_annotation_prompt: str = \
'''
You are an AI visual assistant that can analyze 2D maps. 
You are provided with a satellite image of an urban area, which is fetched from the Google Maps static map API. 
There might be some text and markers in the image, denoting the names of streets, buildings, and other landmarks.
Besides, the longitude and latitude of the center of the image are also provided by user.
Based on your knowledge of the area and the provided information, please give a brief description of the urban area. 
Please keep it short and concise (in 1~2 sentences), while expressing the most important and relevant feature of this area.
DO NOT repeat the information provided by the user.
'''
    city_recommendation_prompt: str = \
'''
You are an AI assistant that is familier with cities all around the world. 
Please recommend some spots in arbitary cities that have distinct features and are worth visiting.
List name of the spots (which can be used as a search key word for geocoding) in a single line, seperated by a single verticle dash: '|'.
Avoid recommending same or similar districts.
DO NOT show preference over any specific city or country.
Example: 1600 Amphitheatre Parkway, Mountain View, CA, USA | Eiffel Tower, Paris, France
'''

# A refactored version of ChatBot with the same add_prompt and add_message interface but using openai client
class OpenAIChatBot: # gpt-4o-mini or gpt-4o
    def __init__(self, id='', model='gpt-4o-mini-2024-07-18', api_key=None, max_tokens=150, temperature=0.7, top_p=1.0, max_completion_tokens=None, *kwargs):
        self.id = id
        if not api_key:
            api_key = os.environ['OPENAI_API_KEY']
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        self.messages = []
        self.model = model
        self.max_tokens = max_tokens
        self.max_completion_tokens = max_completion_tokens
        self.temperature = temperature
        self.top_p = top_p

    def add_prompt(self, prompt): # System Prompt
        self.prompt = prompt

    def add_message(self, message):
        self.messages.append({'role': 'user', 'content': message})
    
    def load_prompt_and_instruction(self, inst_file):
        with open(inst_file, 'r') as f:
            json_data = json.load(f)
            self.prompt = json_data['prompt']
            self.instruction = json_data['instruction']

    def load_prompt_and_instruction_sub_task_gen(self, sub_task_system_prompt, sub_task_gen_prompt):
        if self.id == 'sub_task_gen':
            self.prompt = sub_task_system_prompt
            self.add_message(sub_task_gen_prompt)
        else:
            print('Not Supported Yet')

    def send(self, **kwargs):
        
        if "response_format" in kwargs:
            if self.max_completion_tokens == None:
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[{'role': 'developer', 'content': self.prompt}] + self.messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    **kwargs,
                )
                return response.choices[0].message.parsed, response.usage
            else:
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[{'role': 'developer', 'content': self.prompt}] + self.messages,
                    max_completion_tokens = self.max_completion_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    **kwargs,
                )
                return response.choices[0].message.parsed, response.usage
        
        if self.max_completion_tokens == None:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'developer', 'content': self.prompt}] + self.messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                **kwargs,
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'developer', 'content': self.prompt}] + self.messages,
                max_completion_tokens = self.max_completion_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                **kwargs,
            )
    
        return response.choices[0].message.content, response.usage

if __name__ == '__main__':
    chatbot = OpenAIChatBot(id='recommender', model='gpt-4o-mini')
    chatbot.load_prompt_and_instruction('configs/spot_and_question_gen.json')
    print(chatbot.send())
