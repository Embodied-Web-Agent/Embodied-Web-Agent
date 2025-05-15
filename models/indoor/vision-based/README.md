
## Install
```bash
# Python 3.10 (or 3.11, but not 3.12 cause 3.12 deprecated distutils needed here)
python -m venv venv
source venv/bin/activate
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

3. set up OPENAI_API_KEY in your environment

6. Launch the evaluation
```bash
python run_embodied.py \
  --instruction_path agent/prompts/jsons/p_som_cot_id_actree_3s_web_agent \ 
  --test_start_idx 1 \
  --test_end_idx 912 \
  --model gpt-4o \
  --result_dir <your_result_dir>
```
