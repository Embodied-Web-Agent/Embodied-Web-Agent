import re
from openai import OpenAI
import google.generativeai as genai
from google.generativeai import GenerativeModel
import time
import random
from google.api_core.exceptions import RetryError, ServiceUnavailable

from utils import parse_prediction, clean_brackets, run_vwa
from prompt import *


'''Convert model name to API style'''
def model_family_to_api_style(model):
    if model.startswith("gpt"):
        return "gpt"
    elif model.startswith("gemini"):
        return "gemini"
    elif model.startswith("qwen"):
        return "gpt"
    elif model.startswith("internvl"):
        return "gpt"
    else:
        raise ValueError(f"Unknown model: {model}")


'''Format text appropriately for the model family'''
def format_text(text, model_family='gpt'):
    # - For 'gpt': wraps text with {"type": "text", "text": text}
    # - For 'gemini': returns raw text
    if model_family == 'gemini':
        return text
    elif model_family == 'gpt':
        return {"type": "text", "text": text}


'''Class for the agent'''
class Agent:
    def __init__(self, client, model, model_family):
        self.client = client
        self.model = model # exact model, e.g., gpt-4o, gemini-2.0-flash, qwen-vl-plus, internvl2.5-latest
        self.model_family = model_family # model family, eg. gpt, gemini

    def generate_action(self, valid_actions, init_node_id, curr_node_id):
        prompt = GENERATE_ACTION.format(initial_id=init_node_id, current_id=curr_node_id, actions=valid_actions)
        response = self.call_vlm(prompt)
        action = self.parse(response, 'action')
        return action

    def generate_web_query(self, image_messages, web_context):
        if self.model_family == 'gpt' or self.model_family == 'qwen':
            # Only include text entries
            query_history_entries = [entry["text"] for entry in web_context if isinstance(entry, dict) and entry.get("type") == "text"]
        elif self.model_family == 'gemini':
            # web_context is a list of strings already
            query_history_entries = web_context

        query_history_str = "\n".join(f"{i+1}. {entry}" for i, entry in enumerate(query_history_entries))
        response = self.call_vlm(GENERATE_WEB_QUERY.format(query_history=query_history_str), context=image_messages)
        web_query = self.parse(response, 'web_query')
        return web_query

    def evaluate_confidence(self, image_messages, web_context):
        temp_context = web_context.copy()
        full_context = list(image_messages) 
        if web_context:
            temp_context.append(format_text("Here are some relevant web search results.", model_family=self.model_family))
            full_context.extend(temp_context)

        response = self.call_vlm(ESTIMATE_CONFIDENCE, context=full_context)
        confidence = self.parse(response, 'confidence')
        return confidence
    
    def generate_prediction(self, full_context):
        if self.model == 'qwen':
            generate_prediction_prompt = GENERATE_PREDICTION_QWEN
        else: 
            generate_prediction_prompt = GENERATE_PREDICTION
        response = self.call_vlm(generate_prediction_prompt, context=full_context)
        prediction = parse_prediction(response)
        return response, prediction
    
    def call_vlm(self, prompt, max_tokens=400, temperature=0.7, context=None):
        api_style = model_family_to_api_style(self.model_family)
        if api_style == 'gpt':
            return self.call_gpt_base(prompt, self.model, max_tokens, temperature, context)
        if api_style == 'gemini':
            return self.call_gemini(prompt, self.model, max_tokens, temperature, context)
        
    def call_gpt_base(self, prompt, model, max_tokens=400, temperature=0.7, context=None):
        message_content = [{"type": "text", "text": prompt}] 
        if context:
            message_content += context 
        message_content = [c for c in message_content if c is not None]

        # print(f"Calling GPT base with content: {message_content}")
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user", 
                    "content": message_content
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return (response.choices[0].message.content)
    
    def call_gemini(self, prompt, model, max_tokens=400, temperature=0.7, context=None, retries=3, backoff_base=2.0):
        content = [prompt]
        if context:
            content += context
        content = [c for c in content if c is not None]
        
        for attempt in range(1, retries + 1):
            try:
                response = self.client.generate_content(contents=content)
                return response.text

            # Typical transient Gemini transport errors
            except (RetryError, ServiceUnavailable) as e:
                if attempt == retries:
                    raise e
                delay = backoff_base * attempt + random.uniform(0, 1)
                print(f"[Gemini] attempt {attempt} failed ({e}); retrying in {delay:.1f}s")
                time.sleep(delay)

            except Exception:
                # Any other unexpected error
                raise

    def parse(self, output, kind):
        if kind == 'action':
            reasoning_match = re.search(r"Reasoning Steps:\s*(.*?)(?=\nAction:)", output, re.DOTALL)
            action_match = re.search(r"^Action:\s*(.*)$", output, re.MULTILINE)

            reasoning_text = reasoning_match.group(1).strip() if reasoning_match else ""
            value = action_match.group(1).strip() if action_match else None
            return value

        elif kind == 'web_query':
            # print(f"Web Query Raw: {output}")
            reasoning_match = re.search(r"Reasoning Steps:\s*(.*?)(?=\nIntent Template:)", output, re.DOTALL)
            intent_template_match = re.search(r"Intent Template:\s*(.*)", output)
            intent_match = re.search(r"Intent:\s*(.*)", output)
            element_match = re.search(r"Element:\s*(.*)", output)
            string_note_match = re.search(r"String Note:\s*(.*)", output)

            reasoning_text = reasoning_match.group(1).strip() if reasoning_match else ""
            intent_template = clean_brackets(intent_template_match.group(1).strip() if intent_template_match else "")
            intent = clean_brackets(intent_match.group(1).strip() if intent_match else "")
            element = clean_brackets(element_match.group(1).strip() if element_match else "")
            string_note = clean_brackets(string_note_match.group(1).strip() if string_note_match else "")
            return {
                "intent_template": intent_template,
                "intent": intent,
                "element": element,
                "string_note": string_note
            }
        
        elif kind == 'confidence':
            reasoning_match = re.search(r"Reasoning Steps:\s*(.*?)(?=\nConfidence:)", output, re.DOTALL)
            confidence_match = re.search(r"Confidence:\s*(High|Medium|Low)", output)

            reasoning_text = reasoning_match.group(1).strip() if reasoning_match else ""
            value = confidence_match.group(1).strip() if confidence_match else None
            return value


'''Check Confidence'''
def is_confident(A, image_messages, web_context, move_history):
    confidence = A.evaluate_confidence(image_messages, web_context)
    move_history.append('Estimating Confidence: ' + str(confidence))
    # print(f'Confidence: {confidence}')

    if confidence == 'High':
        return True
    else:
        return False


'''Run a web query and get the result'''
def do_web_query(A, image_messages, web_context, move_history, max_tries=2, max_new_queries=2):
    # Get web search query (intent_tmemplate, element, intent, string_note)
    for query_attempt in range(max_new_queries + 1):
        web_query = A.generate_web_query(image_messages, web_context)
        print(f"Web Query: {web_query['intent']}")

        # Run VWA and get result
        vwa_result, query_id = run_vwa(web_query, max_tries=max_tries, model_family=A.model_family)

        if is_vwa_success(vwa_result) and vwa_result != "":
            web_context.append(format_text(f"{web_query['intent']}: {vwa_result}", model_family=A.model_family))
            move_history.append(f"Querying Web: {web_query['intent']}")
            move_history.append(f"Web Query ID: {query_id}")
            move_history.append(f"Web Query Response: {vwa_result}")
            print(f"Web Query Answer: {vwa_result}")
            return

        print(f"Web Query Failed (ID: {query_id}): {vwa_result}")

    web_context.append(format_text(f"{web_query['intent']}: {vwa_result}", model_family=A.model_family))
    move_history.append(f"Querying Web: {web_query['intent']}")
    move_history.append(f"Web Query ID: {query_id}")
    move_history.append(f"Web Query Response (final fallback): {vwa_result}")
    print(f"[VWA] Final fallback result used: {vwa_result}")
    return


def is_vwa_success(vwa_result):
    known_failures = [
        "Early stop",
        "Same typing action for 5 times",
        "Failed to parse actions for 3 times",
        "ERROR: No parsed_action found",
        "ERROR: Empty parsed_action",
        "ERROR: VWA subprocess timed out",
    ]
    return not any(err.lower() in vwa_result.lower() for err in known_failures)