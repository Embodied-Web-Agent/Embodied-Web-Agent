CUDA_VISIBLE_DEVICES=0 python web_interaction.py \
  --instruction_path agent/prompts/jsons/p_som_cot_id_actree_3s.json \
  --test_start_idx 0 \
  --test_end_idx 1 \
  --result_dir results/test_wiki_som/ \
  --test_config_base_dir=config_files/ewa_outdoor/test_wikipedia \
  --model gpt-4-turbo-2024-04-09 \
  --action_set_tag som  --observation_type image_som 