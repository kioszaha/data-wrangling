# 🛖 Airbnb Dataset

Source - [Inside Airbnb](https://insideairbnb.com/new-zealand/)
Column data obtained from [Inside Airbnb Data Dictionary](https://docs.google.com/spreadsheets/d/1iWCNJcSutYqpULSQHlNyGInUvHg2BoUGoNRIGa6Szc4)

## 📜 Documentation

# Data Cleaning for Airbnb Combined Dataset

File:.output/combined_listing.csv

## Columns Dropped

1. Neighbourhood_group 

Reason: Every Value is "Christchurch City" data is redundent anyless population changes to include more regions.

2. License 

Reason: 100% of the Data in License column was missing.

3. Host_Name

Reason: Redundant column becaue host_id already uniquly identifies each host. 

## Dropped Rows

1. Minimum_nights (Lost 37 Rows)

Reason: Only 37 missing rows and there is no sensible value to replace it with.

2. Price (Lost 10639 Rows)

Reason: Next's week's deliverable will be on Rental Price vs Availble Properties. Having missing data is not useful for next weeks goal. 

## Filled Values

1. Reviews_per_month with 0

Reason: I'm assuming that having missing values here indicts a real value. e.g There has been zero reviews this month.  

## Notes

1. Thought about removing ID but decided against it becasue it could be useful for organsing data later on

# Consequnces

1. Total number of columns has been reduced from 20 to 17.
2. 10,639 rows were dropped due to missing price, alongside 37 rows due to missing minimum_nights. In total 10,676 rows were dropped.

| Column                         | Description                                                                                                                                                                             |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| id                             | Airbnb's unique identifier for the listing                                                                                                                                              |
| name                           | Name of the listing                                                                                                                                                                     |
| host_id                        | Airbnb's unique identifier for the host/user                                                                                                                                            |
| host_name                      | Name of the host. Usually just the first name(s).                                                                                                                                       |
| neighbourhood_group            | High level city/district of the listing                                                                                                                                                 |
| neighbourhood                  | Suburb/subdistrict of the listing                                                                                                                                                       |
| latitude                       | Latitude coordinate of the Airbnb property                                                                                                                                              |
| longitude                      | Longitude coordinate of the Airbnb property                                                                                                                                             |
| room_type                      | All homes are grouped into the following three room types: Entire place, Private room, and Shared room                                                                                  |
| price                          | Daily price in local currency                                                                                                                                                           |
| minimum_nights                 | minimum number of night stay for the listing (calendar rules may be different)                                                                                                          |
| number_of_reviews              | The number of reviews a listing has                                                                                                                                                     |
| last_review                    | The date of the last/newest review                                                                                                                                                      |
| reviews_per_month              | The average number of reviews per month the over the lifetime of the listing.                                                                                                           |
| calculated_host_listings_count | The number of listings the host has in the current scrape, in the city/region geography.                                                                                                |
| availability_365               | The availability of the listing 365 days in the future as determined by the calendar. Note a listing may not be available because it has been booked by a guest or blocked by the host. |
| number_of_reviews_ltm          | The number of reviews the listing has (in the last 12 months)                                                                                                                           |
| license                        | The licence/permit/registration number                                                                                                                                                  |

## 🪡 Filtering Decisions
