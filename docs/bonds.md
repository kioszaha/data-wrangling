# 🛖 Quarterly Tenancy

Data Source - [Tenancy Services: Rental bond data](https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/), published by the Ministry of Business, Innovation and Employment.

Used under Creative Commons Attribution 3.0 New Zealand License

## 📜 Documentation

Documentation for this dataset was compiled using the following web pages:

- [https://www.tenancy.govt.nz/rent-bond-and-bills/market-rent/market-rent-explained/](https://www.tenancy.govt.nz/rent-bond-and-bills/market-rent/market-rent-explained/)
- [https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/](https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/)

| Column                  | Description                                                                                                                                                                  |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TimeFrame               | The quarter this row covers, shown as the quarter's start date (e.g. 2026-04-01 = Q2 2026, Apr–Jun)                                                                          |
| Location Id             | SA2-2019 area code (Statistics NZ statistical area). `-99` = New Zealand-wide total                                                                                          |
| Dwelling Type           | Property type: House/Townhouse, Apartment, Flat, Room, Boarding House, or `ALL` (all types combined)                                                                         |
| Number Of Beds          | Number of bedrooms (0–9, or 5+), or `ALL` for every bedroom count combined                                                                                                   |
| Total Bonds             | Number of new bonds lodged in that quarter, for that location/dwelling type/bed count                                                                                        |
| Active Bonds            | Number of bonds that were current (in effect) at some point during that quarter                                                                                              |
| Closed Bonds            | Number of bonds closed/refunded during that quarter                                                                                                                          |
| Median Rent             | The standard statistical median of weekly rent, from bonds lodged in that quarter                                                                                            |
| Geometric Mean Rent     | Exponential of the mean of log-transformed weekly rents, useful for reducing skew caused by rent values clustering around round dollar amounts                               |
| Upper Quartile Rent     | Synthetic 75th percentile weekly rent (in NZD). Parametrically estimated assuming a log-normal rent distribution to smooth out artificial price clustering at round numbers. |
| Lower Quartile Rent     | Synthetic 25th percentile weekly rent (in NZD). Parametrically estimated assuming a log-normal rent distribution to smooth out artificial price clustering at round numbers. |
| Log Std Dev Weekly Rent | Standard deviation of the natural log of weekly rent, indicates price dispersion/variance within that location and dwelling category                                         |
| beds_num                | A column added by our transformations, this is a numerical version of the Number Of Beds column. Note "ALL", "5+", and missing source values are assigned to NA.             |

## 🪡 Filtering Decisions

The raw file contained 226,080 rows. After cleaning, the dataset has 27,118 rows (retained 11.99% of the original data).

### TimeFrame

We retained every quarterly record whose quarter overlaps 5 October 2025 to 19 June 2026, the date range covered by the Airbnb snapshots. Because `TimeFrame` stores the quarter start date, this includes Q4 2025 (`2025-10-01`), Q1 2026, and Q2 2026.

This filtering decision dropped 198,868 rows (87.96%).

### Location ID

Location ID seems to be a critical column in ongoing analysis, so we dropped any rows where Location ID is missing.

`Location Id = -99` represents the New Zealand-wide total. There are 127 such rows in the retained period. These rows are retained for now because the assignment requires retaining `Location Id`, but they must be excluded when restricting the bond data to Christchurch for the comparison analysis.

This filtering decision dropped 94 rows (0.35%).

### Number Of Beds

The dataset originally provided this as a categorical string column. The unique values were:

['1', '2', '3', '4', '5', '9', 'ALL', '5+', '6', nan, '0', '7', '15', '8']

We retain the original `Number Of Beds` labels and add `beds_num` for numerical bedroom analysis.

The open-ended '5+' is retained in the original `Number Of Beds` column but is represented as missing in `beds_num`; we did not assume that it equals a particular numeric value.

We initially intended to drop rows with 'ALL' as the Number of Beds. Instead, we retained these aggregate rows in the original `Number Of Beds` column and represented them as missing in `beds_num`.

The `Number Of Beds` field has 876 missing values in the retained period. These rows were kept because their other measures remain usable; their `beds_num` value is missing. Overall, `beds_num` has 11,911 missing values: 10,764 `ALL` rows, 271 `5+` rows, and 876 rows missing the source bedroom value.

### Median Rent

We dropped rows with missing `Median Rent`, since rent is a core measure for the planned comparison. No retained-period rows met this condition.
