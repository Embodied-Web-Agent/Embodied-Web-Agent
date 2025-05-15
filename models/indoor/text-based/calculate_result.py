import json
import os

scores = []
for file in os.listdir("./results"):
    if not file.endswith(".json"): continue
    try:
        score = json.load(open(f"results/{file}"))["score"]
        print (score)
        print (json.load(open(f"results/{file}"))["state_evaluator"])
    except:
        pass
    scores.append(score)
print (sum(scores) / len(scores))
