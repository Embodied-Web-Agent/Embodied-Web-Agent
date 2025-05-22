# Embodied Web Agent - Outdoor Tasks

<i>Embodied Web Agent</i> is a realistic and diverse benchmark bridging the real-world and digital world. It tests model's ability to handle tasks from real and virtual world in an intertwined manner.

Here is the instruction to help you better understand how to use our code.

## Install
```bash
# Python 3.10 (or 3.11, but not 3.12 cause 3.12 deprecated distutils needed here)
conda create -n ewa python=3.10; conda activate ewa
pip install -r requirements.txt
playwright install
pip install -e .
```

## Websites Set Up

Please refer to [WebArena](https://github.com/web-arena-x/webarena/blob/main/environment_docker/README.md) to have a basic idea of how to set up the Amazon EC2 then host the websites.

Right now, our websites are hosted by ourselfves on this [LINK](http://98.80.38.242:1220/). But it is likely to change. In case the websites are down, the best way is to host these websites by yourself. Our websites are built upon webarena series work. After configuring their websites, you can follow our instructions in web_environments part to add our new websites.

In order to configurate the urls for each website, you can simply use our existing urls:
```bash
source models/outdoor/scripts/config_url.sh
```

If you would like to custimize your own websites, you can replace the urls in this script with your own.

`WARNING:` Some of our websites (Wikipedia and OpenStreetMap) are hosted by CMU WebArena Team but their team haven't been maintaining and supporting the codebase and websites actively. Thus, some websites like OpenStreetMap might be down. In oreder to fundanmentally solve this problem, we plan to host all these websites by ourselves. But for now, if the OpenStreetMap hosted by CMU is down, we suggest you utilize real OpenStreetMap website (www.openstreetmap.org) instead. Although the real map website is different from sandbox map website, it can also be used to run some experiments and see some results to have a deeper understanding of how the web agent works.

## Set up API Keys

Since we are using four different models to conduct experiments, we need to config four api keys for them. Remember to set up these api keys ahead of the experiments.

Take the openai api key as an example, you can either directly set up it in the following way:
```bash
export OPENAI_API_KEY=your_key
```
or you can save it in a script file and run it:
```bash
source scripts/openai_key.sh
```

If you don't have an api key right now, you can apply for them in respective websites of these models.

## Data Generation

**You can skip this section since we already generated data.** In case you are interested in the generation process, we can briefly talk about it here.

By using the auto_generator below, we can generate the first version of data. Then based on it, we need to do some human verification.

```bash
#!/bin/bash
# This script runs the auto_generator.py with specified command line parameters.

python navigation/target_gen/auto_generator.py \
  --threshold 10 \
  --coefficient 8.0 \
  --num_sample 5 \
  --start_id 0 \
  --temperature 1.0 \
  --data_folder navigation/data_collection \
  --navi_dump_folder navigation/data_collection/navi_env4 \
  --traj_dump_folder navigation/data_collection/navi_traj4 \
  --prompt_load_path navigation/data_collection/prompt/spot_and_question_gen_v2.json \
  --anno_dump_folder navigation/data_collection/navi_anno4 \
  --logger_dump_folder navigation/data_collection/logger4
```

The threshold is used to sample the start point. The coefficient is used to control the size/area of the generated outdoor environment (i.e., the area of the graph).

In the auto_generator file, the first thing is to generate some source, target coordinate points and corresponding task intents. After collecting batch of them, we generate the subtask intents, which are specific intents for embodied and web operation. Once finish the data generation, we will visualize them and do some human verification. After data generation, we will start to run the experiments and evaluate model performance.

In summary, all files under `navigation/targer_gen` folder are working on data generation. You can see our data sample under `data_collection` folder; task and subtask generation prompt under `data_collection/prompt` folder.


## Web Interaction

The web interaction borrows from visualwebarena code. The goal of this part is to let agent interact with the websites to extract relevant information then solve the problem.

```bash
CUDA_VISIBLE_DEVICES=0 python web_interaction.py \
  --instruction_path models/outdoor/agent/prompts/jsons/p_som_cot_id_actree_3s.json \
  --test_start_idx 0 \
  --test_end_idx 1 \
  --result_dir results/test_map_som/ \
  --test_config_base_dir=config_files/ewa_outdoor/test_map \
  --model gpt-4-turbo-2024-04-09 \
  --action_set_tag som  --observation_type image_som 
```

You can have a try to execute this script to have a better undertsanding of how it works. It is noted that you may need to change the file path. Also, you need to have a gpu to run this code. Finally, you can obtain a result folder, which contains a html file tracking all your steps.

## Outdoor Navigation

This part is outdoor navigation in our outdoor environment.

```bash
#!/bin/bash
# This script runs the outdoor_navigation.py with specified command line parameters.

python models/outdoor/navigation/outdoor_navigation.py \
  --model_name gpt-4o-mini-2024-07-18 \
  --max_tokens 300 \
  --temperature 1.0 \
  --max_steps 100 \
  --map_screenshot_path /path/to/map_screenshot/map_screenshot_x.png \
  --environments_path /path/to/navigation/data_collection/shopping_env_x.json \
  --traj_path /path/to/navigation/data_collection/shopping_traj_x.json
```

You need to specify some file paths then run the code. The map screenshot is the last-step result from the web agent, depicting the navigation directions. The agent needs to follow these directions to navigate to the destination. Environment is the outdoor environment where the agent navigates. It is a graph structure. Traj_path is the path to ground truth trajectories files. The reason why we need it is because it can provide us with the initial heading angle, which is crucial for navigation task.

After running this code, you will get the trajectory of the navigation. There are some sample results under `models/outdoor/navigation/results` folder. The result is a sequence of coordinates and corresponding task_id.

## Inference Pipeline

This section is the code unifying outdoor navigation and web interaction. You can try to execute the script below.

```bash
bash scripts/run_inference.sh
```

It is still noted that you need to finish config everything before running the code.

You can download data and save them in `models/outdoor/navigation/data_collection` folder. For the results, you can create a new folder as your will.

## Acknowledgements

Our code is based on the <a href="https://github.com/web-arena-x/webarena">WebArena codebase</a>. Thanks for their great work!
