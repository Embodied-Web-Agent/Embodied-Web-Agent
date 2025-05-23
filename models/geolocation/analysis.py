import os
import json
import pandas as pd
import unicodedata
from math import radians, sin, cos, sqrt, atan2
import matplotlib.pyplot as plt
import argparse

def load_exclude_ids(args) -> set[int]:
    """Return a set of standpoint_ids to ignore, based on CLI flags."""
    exclude = set()
    if args.exclude_ids:
        exclude |= {int(x) for x in args.exclude_ids.split(',') if x.strip()}
    return exclude

# Process result.json files into dataframe
def process_input_dir(input_dir):
    results = []

    # Look for result.json files in multiple_views folder
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file == 'result.json':
                file_path = os.path.join(root, file)

                # Load JSON file
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Flatten structure for dataframe
                result = {
                    "standpoint_id": data.get("standpoint_id"),
                    "gt_coords": data["ground_truth"].get("coords"),
                    "gt_continent": data["ground_truth"].get("continent"),
                    "gt_country": data["ground_truth"].get("country"),
                    "gt_city": data["ground_truth"].get("city"),
                    "gt_street": data["ground_truth"].get("street"),
                    "gpt_continent": data["gpt_output"]["location"].get("continent"),
                    "gpt_country": data["gpt_output"]["location"].get("country"),
                    "gpt_city": data["gpt_output"]["location"].get("city"),
                    "gpt_street": data["gpt_output"]["location"].get("street"),
                    "gpt_reasoning": data["gpt_output"].get("reasoning"),
                    "gpt_coords_lat": data["gpt_output"]["coords"].get("lattitude"),
                    "gpt_coords_lon": data["gpt_output"]["coords"].get("longitude"),
                    "num_adjacent_standpoints": data.get("num_adjacent_standpoints")
                }
                results.append(result)

    results_df = pd.DataFrame(results)
    return results_df

# Process text -- remove accents from strings
# Source: https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string
def normalize_text(text):
    if type(text) != str:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )

# Analyze results
def analyze_results(df, label="Overall"):
    total = len(df)

    if total == 0:
        print(f"\n--- {label} ---")
        print("No data available.\n")
        return

    # Individual metrics
    pct_continent = df["continent_match"].mean()
    pct_country = df["country_match"].mean()
    pct_city = df["city_match"].mean()
    pct_street = df["street_match"].mean()

    # Specific match combinations
    # pct_all_wrong = (~df["continent_match"] & ~df["country_match"] & ~df["city_match"] & ~df["street_match"]).mean()
    # pct_only_continent_correct = (df["continent_match"] & ~df["country_match"] & ~df["city_match"] & ~df["street_match"]).mean()
    # pct_only_continent_country_correct = (df["continent_match"] & df["country_match"] & ~df["city_match"] & ~df["street_match"]).mean()
    # pct_only_continent_country_city_correct = (df["continent_match"] & df["country_match"] & df["city_match"] & ~df["street_match"]).mean()
    # pct_continent_country_not_city = (df["continent_match"] & df["country_match"] & ~df["city_match"]).mean()
    pct_all_correct = (df["continent_match"] & df["country_match"] & df["city_match"] & df["street_match"]).mean()

    # Output
    print(f"\n--- {label} ---")
    print(f"% Continent correct: {pct_continent:.2%}")
    print(f"% Country correct: {pct_country:.2%}")
    print(f"% City correct: {pct_city:.2%}")
    print(f"% Street correct: {pct_street:.2%}")
    # print(f"% All wrong: {pct_all_wrong:.2%}")
    # print(f"% Only continent correct: {pct_only_continent_correct:.2%}")
    # print(f"% Only continent and country correct: {pct_only_continent_country_correct:.2%}")
    # print(f"% Only continent, country, and city correct: {pct_only_continent_country_city_correct:.2%}")
    print(f"% All correct: {pct_all_correct:.2%}")
    print(f"Total number of results: {total}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', type=str, required=True, help='path to the input directory')
    parser.add_argument('--exclude_ids', help='comma-separated list of standpoint_ids to drop')
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        raise ValueError(f"Invalid input directory: {args.input_dir}")

    print(f"Processing input directory: {args.input_dir}")

    input_dir = args.input_dir
    exclude_ids = load_exclude_ids(args)
    results_df = process_input_dir(input_dir)

    if exclude_ids:
        print(f"Excluding {len(exclude_ids)} standpoint_ids: "
              f"{sorted(exclude_ids)[:10]}{'…' if len(exclude_ids)>10 else ''}")
        results_df = results_df[~results_df['standpoint_id'].isin(exclude_ids)]

    # Process continent/country/city/street
    results_df["gt_continent_norm"] = results_df["gt_continent"].apply(normalize_text)
    results_df["gpt_continent_norm"] = results_df["gpt_continent"].apply(normalize_text)

    results_df["gt_country_norm"] = results_df["gt_country"].apply(normalize_text)
    results_df["gpt_country_norm"] = results_df["gpt_country"].apply(normalize_text)

    results_df["gt_city_norm"] = results_df["gt_city"].apply(normalize_text)
    results_df["gpt_city_norm"] = results_df["gpt_city"].apply(normalize_text)

    results_df["gt_street_norm"] = results_df["gt_street"].apply(normalize_text)
    results_df["gpt_street_norm"] = results_df["gpt_street"].apply(normalize_text)

    # Check if ground truth and GPT values match
    results_df["continent_match"] = (results_df["gt_continent_norm"] == results_df["gpt_continent_norm"])
    results_df["country_match"] = (results_df["gt_country_norm"] == results_df["gpt_country_norm"])
    results_df["city_match"] = (results_df["gt_city_norm"] == results_df["gpt_city_norm"])
    results_df["street_match"] = (results_df["gt_street_norm"] == results_df["gpt_street_norm"])

    # Process ground truth coords
    results_df["gt_coords_lat"] = results_df["gt_coords"].apply(lambda x: float(x.split(",")[0]))
    results_df["gt_coords_lon"] = results_df["gt_coords"].apply(lambda x: float(x.split(",")[1]))
    # results_df["gt_gpt_coords_haversine_dist"] = results_df.apply(get_haversine_distance, axis=1)

    # Save results to CSV
    results_df.to_csv(f"results_{input_dir.replace('/', '_')}.csv", index=False)
    results_df.head(30)

    analyze_results(results_df, label=input_dir)

if __name__ == "__main__":
    main()