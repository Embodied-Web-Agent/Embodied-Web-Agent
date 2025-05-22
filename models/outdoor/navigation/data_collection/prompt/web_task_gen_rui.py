# This actually the prompt for sub-task generation

################## V2 ************************
SUB_TASK_SYSTEM_PROMPT_V2 = \
"""You are an Embodied Web Agent capable of obtaining information from webpages and executing tasks within an embodied environment. I will provide you with a generated_instruction and a generated_name from the embodied environment. The generated_instruction is a description of the task that outlines what the embodied agent needs to do, while the generated_name is the name or address of a location that the embodied agent needs to go to.
"""

SUB_TASK_GEN_PROMPT_V2 = \
"""Based on the generated_instruction and generated_name, you need to generate tasks that both the web and the embodied agent must execute. These tasks should ensure that after execution, the embodied web agent can obtain information from the web to assist in completing the task in the embodied environment.

You must ensure that the generated task intents clearly describe the task that the embodied web agent needs to perform and that they make use of information obtained by interacting with the web. Please note that the task intents should be concise instructions capable of guiding the embodied web agent in executing specific operations.

In addition, the content within the task intents must be actionable, clear, unambiguous, and unique, without any vague language, multiple interpretations, or ambiguity.

We have four types of webpages, and I will provide you with a task category. Based on the task category, you need to generate one or more tasks that interact with the webpages. The tasks must make use of at least one of the following webpages (or multiple):
Task categories include: Cooking, Shopping, Navigation, Traveling, and GeoGuessr.

The descriptions for these task categories are as follows:
	1.	Cooking: You need to search for recipes, cooking methods, ingredients, etc., on the web to help the indoor embodied agent complete cooking tasks.
	2.	Shopping: You need to search for product information, prices, store locations on the web. Then compare this information to find the most suitable store. Finally, the outdoor embodied agent can use the store address from the web to reach the store.
	3.	Navigation: You need to search for maps and route planning on the web. These details will help the outdoor embodied agent find the best route from the current location to the destination.
	4.	Traveling: You need to search for tourist attractions, travel guides, local culture, etc., on the web. Then, this information will help the outdoor embodied agent plan an itinerary and choose attractions or activities.
	5.	GeoGuessr: You need to search for geographical location details, map specifics, street view information, etc., on the web to help the outdoor embodied agent determine its current location.

Please note that the generated tasks must be as specific and clear as possible so that the embodied web agent can execute them. The task description should succinctly explain the task that must be completed.

The types of webpages include: Recipe, Shopping, OpenStreetMap, Wikipedia, and Homepage.
Here are descriptions of these webpages:
	1.	Recipe: This is a recipe website that provides various recipes and cooking methods. You can search for ingredients, cooking techniques, and cooking steps here.
	2.	Shopping: This is a shopping website that provides information on various products, including prices and store locations. You can look for detailed product information and purchasing options here.
	3.	OpenStreetMap: This is an OpenStreetMap website, which provides maps and route planning services. You can search for your current location, destination, and best routes here.
	4.	Wikipedia: This is a Wikipedia website that provides encyclopedic knowledge on various topics. You can look up tourist attractions, local culture, travel guides, and more.
	5.	Homepage: This is a homepage website that provides links to the above websites. These websites can also lead you back to this homepage, making it convenient for users to switch between different websites.

Below are three examples. You need to generate output in this format:

Example 1: 
Task Category: Navigation
generated_instruction: I'd like to go to the grand museum that houses an extensive collection of art from various cultures and eras, set in a stunning Beaux-Arts building adjacent to a famous urban park, making it a cultural landmark.
generated_name: 1000 5th Ave, New York, NY 10028
embodied_task_intent_0: I would like to go to the Metropolitan Museum of Art.
web_task_intent_1: Search for the best route from my current location to the Metropolitan Museum of Art using the OpenStreetMap website. Provide me with the directions.

Example 2:
Task Category: Traveling
generated_instruction: I'd like to visit the iconic Central Park, a sprawling urban park in New York City, known for its picturesque landscapes, recreational activities, and cultural landmarks.
generated_name: Central Park, New York, NY
web_task_intent_0: Search for information about Central Park on the Wikipedia website. I would like to know about its open hours.
embodied_task_intent_1: I would like to explore Central Park and its various attractions.
web_task_intent_2: Find the best walking route between my current location and Central Park using the OpenStreetMap website.

Example 3:
Task Category: Shopping
generated_instruction: I need to get from CVS Pharmacy, 65, 5th Avenue, Manhattan, New York to Whole Foods Market, 4, East 14th Street, Manhattan, New York.
generated_name: Whole Foods Market, 4, East 14th Street, Manhattan, New York
web_task_intent_0: Buy one 500g cheese with the lowest price.
web_task_intent_1: Provide me with the shortest route from CVS Pharmacy, 65, 5th Avenue, Manhattan, New York to Whole Foods Market, 4, East 14th Street, Manhattan, New York.
embodied_task_intent_2: I would like to go from CVS Pharmacy, 65, 5th Avenue, Manhattan, New York to Whole Foods Market, 4, East 14th Street, Manhattan, New York.
web_task_intent_3: Tell me how much calories are in 500g mozzarella cheese.

Please Note:
1.	You can generate additional embodied_task_intent and web_task_intent entries, ensuring that each task is independent and associated with the generated_instruction and generated_name. Each task description must be clear and unambiguous, avoiding vague instructions.
2.	The generated intents must strictly follow the naming format: embodied_task_intent_0, web_task_intent_1, embodied_task_intent_2, web_task_intent_3, etc. Then, the content should immediately follow the numbered label, for example:
embodied_task_intent_0: AAAA
web_task_intent_1: BBBB
embodied_task_intent_2: CCCC
web_task_intent_3: DDDD
3. The embodied_task_intent and web_task_intent must generate at least one each. More can be generated for each, but it is also fine to generate just one for each. Generate according to the actual task requirements.

You are given the following inputs:
Task Category: [task_category_placeholder]
generated_instruction: [generated_instruction_placeholder]
generated_name: [generated_name_placeholder]

Please only generate the embodied_task_intent and web_task_intent below. 
You need to strictly follow the format provided above.
"""
