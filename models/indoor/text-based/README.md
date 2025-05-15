## Install
```bash
# Python 3.10+
conda create -n webarena python=3.10; conda activate webarena
pip install -r requirements.txt
playwright install
pip install -e .
```

## End-to-end Evaluation
1. Configurate the urls for each website.
```bash
export RECIPE=http://98.80.38.242:1206
export SHOPPING=http://98.80.38.242:1207
export REDDIT=http://98.80.38.242:9999
export MAP=http://98.80.38.242:3000
export WIKIPEDIA=http://98.80.38.242:8888
export HOMEPAGE=http://98.80.38.242:1220
```

2. Download the config files from https://huggingface.co/datasets/evelynhong/embodied-web-agent-indoor/tree/main/indoor_files and place them in config_files/ 

3. set up OPENAI_API_KEY, GOOGLE_API_KEY, DASHSCOPE_API_KEY in your environment for GPT, Gemini, Qwen respectively. 

6. Launch the evaluation
```bash
python run.py \
  --instruction_path agent/prompts/jsons/p_cot_embodied_web_agent.json \ # p_cot_embodied_web_agent_gemini.json for gemini and p_cot_embodied_web_agent_qwen.json for qwen
  --test_start_idx 1 \
  --test_end_idx 912 \
  --model gpt-4o \
  --result_dir <your_result_dir>
```
