"""
Clean the Christchurch Airbnb listings dataset (Deliverable 4)

Using the combined_listings.csv file from Deliverable 3

"""
import pandas as pd

OUTPUT_PATH = ".output/cleaned_listings.csv"

def clean_data():
    df = pd.read_csv(".output/combined_listings.csv")

    #dropped columns neightbourhood_group & license & host_name
    df = df.drop(columns=["neighbourhood_group", "license", "host_name"])

    #remove missing values
    n_before = len(df)
    df = df.dropna(subset=["minimum_nights"])
    print(f"minimum_nights: {n_before - len(df)}")

    #Filled in missing values for reviews_per_month
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0)

    #remove missing values
    n_before = len(df)
    df = df.dropna(subset=["price"])
    print(f"price: {n_before - len(df)}")

    #save as csv
    df.to_csv(OUTPUT_PATH, index=False)
    return df
 
 
if __name__ == "__main__":
    clean_data()

