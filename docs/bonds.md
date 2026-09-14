## 🛖 Quarterly Tenancy

Source - [Tenancy Services](https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/)


| Column                    | Description                                                                                                   |
|---------------------------|-----------------------------------------------------------------------------------------------------------------|
| TimeFrame                 | The quarter this row covers, shown as the quarter's start date (e.g. 2026-04-01 = Q2 2026, Apr–Jun)             |
| Location Id               | SA2-2019 area code (Statistics NZ statistical area). `-99` = New Zealand-wide total                             |
| Dwelling Type             | Property type: House/Townhouse, Apartment, Flat, Room, Boarding House, or `ALL` (all types combined)            |
| Number Of Beds            | Number of bedrooms (0–9, or 5+), or `ALL` for every bedroom count combined                                      |
| Total Bonds               | Number of new bonds lodged in that quarter, for that location/dwelling type/bed count                           |
| Active Bonds              | Number of bonds that were current (in effect) at some point during that quarter                                 |
| Closed Bonds              | Number of bonds closed/refunded during that quarter                                                             |
| Median Rent               | The standard statistical median of weekly rent, from bonds lodged in that quarter                               |
| Geometric Mean Rent       | A smoothed alternative to the median (nth root of the product of values) — reduces distortion from rents clustering at round numbers |
| Upper Quartile Rent       | Smoothed estimate of the 75th percentile weekly rent, assuming a log-normal rent distribution                   |
| Lower Quartile Rent       | Smoothed estimate of the 25th percentile weekly rent, assuming a log-normal rent distribution                   |
| Log Std Dev Weekly Rent   | Standard deviation of the log of weekly rent — a measure of how spread out rents are within that group          |