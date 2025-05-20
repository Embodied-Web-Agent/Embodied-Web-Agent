# Geolocation Task
Welcome to our geolocation task, based on the popular online game GeoGuessr. 

The goal of this task is to evaluate a VLM's ability to determine the coordinates (latitude, longitude) and continent, country, city, and street of a particular location sampled from the Breadth dataset introduced in the VLMs as GeoGuessr Masters paper (Huang et al.). 

However, instead of only providing the model with a single image, we allow the model to move from the initial viewpoint to adjacent viewpoints using the Google Street View API—just like how you're able to move along a street in GeoGuessr to explore the location. 

Additionally, we provide our model with web access (Wikipedia) via VisualWebArena and make queries to enhance its predictions (Koh et al.).

# Directions for Running
## Setting Up the Repositories
1. Clone `VisualWebArena (VWA)` in the directory containing the embodied repository
```
git clone https://github.com/web-arena-x/visualwebarena.git
```
2. Follow the `VWA` setup directions (also outlined below)
- Create a `python 3.10` or `python 3.11` virtual environment
- Install required packages
```
cd visualwebarena
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
pip install -e .
```

- Since some of the package requirements in VWA are outdated, run the following as well:
```
pip install --upgrade "transformers>=4.46.0" "tokenizers>=0.19,<0.22" "huggingface-hub>=0.30.2"

# Upgrade torch according to your CUDA version, found using nvidia-smi (e.g. cu124 for CUDA version 12.4)
pip install --upgrade torch --index-url https://download.pytorch.org/whl/<your_cuda_version>

pip install --upgrade tiktoken
```

- Set the following environment variables:
```
export DATASET=visualwebarena
export WIKIPEDIA="<your_wikipedia_domain>:8888"
```

3. Return to the `geoguessr_v2` directory in `embodied` and install the required packages
```
cd ../embodied/tasks/geoguessr_v2
pip install -r requirements.txt
```

4. Create a `.env` file containing the following:
- The Google API key is for using the Google Street View API (REQUIRED)
```
GOOGLE_API_KEY="your_key_here"
OPENAI_API_KEY="<your_key_here>"
```

## Setting up the Data
1. Download `Breadth.xlsx` from the FairLocator repository: https://github.com/limenlp/FairLocator/tree/main/SourceData
2. Create a new folder named `data_source` in the `geoguessr_v2` directory and move `Breadth.xlsx` into the new folder.

## Running the Pipeline
You can now test our full pipeline using `interactive.py` with the following flags:
- `model`: your API of choice (default: gpt)
- `num_samples`: how many samples (max 600) you want to evaluate (default: 200)
- `output_dir`: 
```
python interactive.py --model <api_name> --num_samples <int> --output_dir <dir_name>
```
We also provide `interactive_v2.py` which parallelizes API calls to speed up runs with larger sample sizes.

## Visualize the Results
You can use `Streamlit` to help visualize your results:
```
streamlit run visualization.py
```

# Acknowledgements
We use the Breadth dataset from [FairLocator](https://github.com/limenlp/FairLocator) and the web environment from [VisualWebArena](https://github.com/web-arena-x/visualwebarena?tab=readme-ov-file). 