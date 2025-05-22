# this is the prompt for the general generation task

# v1
# {
#     "prompt": "You are an AI assistant that is familiar with cities all around the world. For a given city, please provide an iconic locations. For each location, provide a navigation instruction that captures its unique characteristics, historical significance, cultural importance, or architectural features WITHOUT directly mentioning its name. The navigation instruction should be specific enough that someone knowledgeable about the city could identify the exact location. Return the results as a JSON list where each element contains 'location' (a searchable address for geocoding) and 'instruction' (an informative instruction that avoids using the location's name but will uniquely locate the location). REMEMBER that the location MUST be in the city of New York, USA! Example: [{\"location\": \"350 5th Ave, New York, NY 10118\", \"instruction\": \"I'm in New York City and I'd like to go to the Art Deco skyscraper from the 1930s that held the title of world's tallest building for nearly 40 years. It has 102 stories and is an enduring symbol of the city's ambition.\"}]",
#     "instruction": "Only give me one spot in one of these cities: New York, USA; Los Angeles, USA; Hong Kong, China; London, UK; Paris, France; Tokyo, Japan; Sydney, Australia; Berlin, Germany; Mumbai, India; Toronto, Canada; Singapore; Seoul, South Korea; Barcelona, Spain; Istanbul, Turkey; Bangkok, Thailand; Sao Paulo, Brazil; Mexico City, Mexico; Manila, Philippines; Zurich, Switzerland; Vienna, Austria."
# }

PROMPT = """You are an AI assistant that is familiar with cities all around the world. 
For a given city, please provide an iconic locations. 
For each location, provide a navigation instruction that captures its unique characteristics, historical significance, cultural importance, or architectural features WITHOUT directly mentioning its name. 
The navigation instruction should be specific enough that someone knowledgeable about the city could identify the exact location. 
Return the results as a JSON list where each element contains 'location' (a searchable address for geocoding) and 'instruction' (an informative instruction that avoids using the location's name but will uniquely locate the location). 
REMEMBER that the location MUST be in the city of New York, USA; Philadelphia, USA; Boston, USA; Pittsburgh, USA!
Here are four examples: 
[{\"location\": \"350 5th Ave, New York, NY 10118\", \"instruction\": \"I'm in New York City and I'd like to go to the Art Deco skyscraper from the 1930s that held the title of world's tallest building for nearly 40 years. It has 102 stories and is an enduring symbol of the city's ambition.\"}]
[{\"location\": \"520 Chestnut St, Philadelphia, PA 19106\", \"instruction\": \"I'm in Philadelphia and I'd like to go to the red-brick Georgian hall with a white steeple in the historic district where revolutionary delegates gathered in the 18th century to debate and adopt the nation's founding documents.\"}]
[{\"location\": \"4 Jersey St, Boston, MA 02215\", \"instruction\": \"I'm in Boston and I'd like to go to the century-old ballpark that opened in 1912, famous for its emerald-green left-field wall and as the longstanding home of one of Major League Baseball's oldest franchises.\"}]
[{\"location\": \"601 Commonwealth Pl, Pittsburgh, PA 15222\", \"instruction\": \"I'm in Pittsburgh and I'd like to go to the 150-foot-tall water jet fountain at the tip of downtown's triangular park, marking where three rivers converge against a backdrop of the city skyline.\"}]
"""

INSTRUCTION = """Only give me one spot in one of these cities: New York, USA; Philadelphia, USA; Boston, USA; Pittsburgh, USA."""