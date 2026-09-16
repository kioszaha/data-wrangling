import os
import time
from multiprocessing import Pool
import requests
import pandas as pd
from config import OUTPUT_DIR

API_KEY = os.getenv("KOORDINATES_API_KEY")
LAYER_ID = 123515


def get_area_code(coords):
    lat, lon = coords
    url = "https://koordinates.com/services/query/v1/vector.json"
    params = {
        "key": API_KEY,
        "layer": LAYER_ID,
        "x": lon,
        "y": lat,
        "max_results": 1,
        "radius": 100,
        "geometry": "false",
        "with_field_names": "true",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        features = data["vectorQuery"]["layers"][str(LAYER_ID)]["features"]
        if not features:
            return None
        return features[0]["properties"].get("SA22026_V1_00")
    except Exception as e:
        print(f"Error for ({lat}, {lon}): {e}")
        return None


def main():
    input_path = OUTPUT_DIR / "cleaned_listings.csv"
    output_path = OUTPUT_DIR / "cleaned_listings_with_area_code.csv"

    df = pd.read_csv(input_path)
    coords = list(zip(df["latitude"], df["longitude"]))

    print(f"Querying area codes for {len(coords)} listings...")
    start = time.time()

    with Pool(processes=8) as pool:
        area_codes = pool.map(get_area_code, coords)

    elapsed = time.time() - start
    print(f"Done in {elapsed:.1f} seconds")

    df["area_code"] = area_codes

    missing = df["area_code"].isna().sum()
    print(f"Missing area codes: {missing} ({missing / len(df):.2%})")

    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()