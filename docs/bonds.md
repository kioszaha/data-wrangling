# 🛖 Quarterly Tenancy

## 📜 Documentation

Source - [('The Ministry of Business, Innovation and Employment')](https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/)

Used under Creative Commons Attribution 3.0 New Zealand License

| Column                  | Description                                                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| TimeFrame               | The quarter this row covers, shown as the quarter's start date (e.g. 2026-04-01 = Q2 2026, Apr–Jun)                                  |
| Location Id             | SA2-2019 area code (Statistics NZ statistical area). `-99` = New Zealand-wide total                                                  |
| Dwelling Type           | Property type: House/Townhouse, Apartment, Flat, Room, Boarding House, or `ALL` (all types combined)                                 |
| Number Of Beds          | Number of bedrooms (0–9, or 5+), or `ALL` for every bedroom count combined                                                           |
| Total Bonds             | Number of new bonds lodged in that quarter, for that location/dwelling type/bed count                                                |
| Active Bonds            | Number of bonds that were current (in effect) at some point during that quarter                                                      |
| Closed Bonds            | Number of bonds closed/refunded during that quarter                                                                                  |
| Median Rent             | The standard statistical median of weekly rent, from bonds lodged in that quarter                                                    |
| Geometric Mean Rent     | A smoothed alternative to the median (nth root of the product of values) — reduces distortion from rents clustering at round numbers |
| Upper Quartile Rent     | Smoothed estimate of the 75th percentile weekly rent, assuming a log-normal rent distribution                                        |
| Lower Quartile Rent     | Smoothed estimate of the 25th percentile weekly rent, assuming a log-normal rent distribution                                        |
| Log Std Dev Weekly Rent | Standard deviation of the log of weekly rent — a measure of how spread out rents are within that group                               |

## 🪡 Filtering Decisions

### TimeFrame

We filtered the bonds dataframe to only contain entries within the date range of 5th October 2025 - 19th June 2026 to ensure we only have entries that overlap with the airbnb data.

This filtering decision dropped 208327 rows (92.15%).

### Location ID

Location ID seems to be a critical column in ongoing analysis, so we dropped any rows where Location ID is missing.

This filtering decision dropped 62 rows (0.35%).

### Number Of Beds

The dataset originally provided this as a categorical string column. The unique values were:

['1', '2', '3', '4', '5', '9', 'ALL', '5+', '6', nan, '0', '7', '15', '8']

In the interest of making sure this data can be used for whatever analysis necessary, we decided to split this into `beds_cat` (categorical) and `beds_num` (numerical) columns.

The open-ended '5+' was dropped from the numerical column as no documentation regarding the actual meaning of this value could be found, and we did not want to assume a value.

We initially intended to drop rows with 'ALL' as the Number of Beds, however we were unsure if Number of Beds would be a crucial part of the analysis we will be doing on the data - and dropping rows with Number Of Beds = "ALL" would have shrunk the data by a further 40% so we have mapped it to the NA value in the numerical column and retained it in the categorical column.

### Median Rent

We went to drop rows with missing Median Rent, but thankfully there were no rows that met this condition.
