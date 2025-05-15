import json

file_a = json.load(open("embodied_score_gpt.json"))
file_b = json.load(open("web_score.json"))

hit = 0
total = 0

for key in file_a:
    embodied_score = file_a[key]
    web_score = file_b[key]
    total += 1

    if web_score and embodied_score == 100:
        hit += 1

print (hit / total)
