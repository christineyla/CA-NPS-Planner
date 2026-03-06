# California National Park Visitation Planner

## Product Requirements Document (PRD)

Version: **1.3**
Status: In Development
Target Release: **9 March 2026**

---

# 1. Executive Summary

The **California National Park Visitation Planner** transforms public data into actionable travel insights.

By combining:

* historical visitation data
* search trends
* weather forecasts
* accessibility information
* seasonal alerts

the system predicts crowd levels at California national parks and recommends optimal travel windows.

The platform converts complex forecasts into simple travel guidance, helping visitors plan trips with lower congestion and better conditions.

---

# 2. Parks in Scope

### Initial parks supported

* Yosemite National Park
* Joshua Tree National Park
* Death Valley National Park
* Sequoia National Park
* Kings Canyon National Park

### Future expansion

* Lassen Volcanic National Park
* Channel Islands National Park
* Redwood National and State Parks
* Pinnacles National Park

---

# 3. Target Users

### Primary User

Traveler / Trip Planner

Typical question:

> “When can I visit Yosemite with minimal crowds?”

### User needs

* predicted crowd levels
* recommended visit windows
* weather expectations
* accessibility information

---

# 4. Forecast Horizon

Forecasts are generated **weekly for the next 26 weeks (6 months).**

Because historical NPS visitation data is monthly, the system uses:

1. **monthly baseline forecasts**
2. **weekly disaggregation**

---

## Historical Data Window

The forecasting system trains on the most recent **10 years of historical data**.

### Visitation Data

* Monthly NPS visitation data
* Approximately **2015–present**

### Weather Data

* Historical temperature and precipitation observations
* Approximately **2015–present**

### Trend Signals

* Google Trends search interest
* Social Media Exposure index

### Data Exceptions

Disruption periods such as **pandemic-era visitation (2020–2021)** may be:

* flagged as anomalies
* downweighted during model training

---

# 5. Core Scoring Metrics

The system calculates four primary scores.

---

## Crowd Score

Range: **0–100**

Calculation:

```
crowd_score = percentile_rank(predicted_weekly_visits within park history)
```

Meaning:

| Score  | Interpretation    |
| ------ | ----------------- |
| 0–30   | Very low crowds   |
| 31–60  | Moderate crowds   |
| 61–80  | Busy              |
| 81–100 | Extremely crowded |

Crowd scores are **relative to each individual park**, not global across parks.

---

## Weather Score

Range: **0–100**

Calculation:

```
weather_score =
0.6 × temperature_comfort +
0.4 × precipitation_factor
```

### Temperature Comfort

| Temperature    | Score |
| -------------- | ----- |
| 55–75°F        | 100   |
| 40–55°F        | 75    |
| 75–85°F        | 70    |
| <40°F or >90°F | 40    |

### Precipitation Factor

| Chance of precipitation | Score |
| ----------------------- | ----- |
| <10%                    | 100   |
| 10–30%                  | 80    |
| 30–60%                  | 50    |
| >60%                    | 20    |

### Weather Forecast Strategy

Because long-range weather forecasts are uncertain:

* Short-range forecasts use actual weather prediction data.
* Longer horizon weeks use **seasonal weather expectations derived from historical averages**.

The weather score therefore reflects **expected comfort conditions rather than exact future weather**.

---

## Accessibility Score

Range: **0–100**

Calculation:

```
accessibility_score =
0.4 × airport_access_score +
0.3 × drive_access_score +
0.2 × road_access_score +
0.1 × seasonal_access_score
```

### Reference Cities

* San Francisco
* Los Angeles
* San Diego
* Sacramento
* Fresno

### Reference Airports

* LAX
* SFO
* SAN
* SMF
* FAT

Users can click **Accessibility Details** to view the breakdown.

---

## Trip Score

Trip Score represents the overall travel desirability of a week.

```
trip_score =
0.6 × (100 − crowd_score) +
0.3 × weather_score +
0.1 × accessibility_score
```

Higher trip score = better week to visit.

---

# 6. Best Weeks to Visit

For each park the system identifies the **top 5 recommended weeks in the next 26 weeks**.

Algorithm:

1. calculate trip score for each week
2. remove weeks with **severe alerts**
3. rank by trip score
4. return top 5

---

# 7. Hidden Gem Weeks

A hidden gem week is defined as:

```
crowd_score < 40
weather_score > 60
```

These weeks offer **low crowds with favorable weather**.

---

# 8. Crowd Calendar

Each park page includes a **26-week crowd calendar**.

Weeks are color coded:

| Color  | Crowd Level       |
| ------ | ----------------- |
| Green  | Low crowds        |
| Yellow | Moderate          |
| Orange | Busy              |
| Red    | Extremely crowded |

Hovering reveals:

* week range
* crowd score
* weather score
* trip score

---

# 9. Homepage Layout

The homepage includes:

### Featured Insight Cards

* Best park to visit this week
* Hidden gem week recommendation
* Lowest crowd score in next 30 days

### Interactive Map

A California map with park markers.

Marker colors represent **current week crowd levels**.

---

# 10. Alerts

The system supports alerts for events such as:

* wildfires
* flooding
* park closures
* road closures
* extreme heat

### Alert Severity

| Level  | Meaning        |
| ------ | -------------- |
| Yellow | Caution        |
| Orange | Disruption     |
| Red    | Avoid visiting |

Red alerts **remove affected weeks from recommendations**.

---

## Alert Categories

| Alert Type   | Example Event                    |
| ------------ | -------------------------------- |
| Wildfire     | wildfire closure or smoke hazard |
| Extreme Heat | dangerous heat advisory          |
| Flooding     | road flooding or storm damage    |
| Road Closure | highway or access road closure   |
| Park Closure | park or area temporarily closed  |

---

# 11. Data Sources

The system aggregates data from multiple public sources.

### National Park Service

* historical visitation dataset

### Search Trends

* Google Trends search interest

### Weather

* historical observations
* short-range weather forecasts

### Accessibility Metadata

* airport proximity
* drive time estimates
* seasonal access constraints

### Social Media Exposure Index (SME)

SME captures online popularity signals.

Sources may include:

* Google Trends search frequency
* social media hashtag volume
* media mentions

SME values are normalized to a **0–100 scale**.

---

# 12. Forecast Model Architecture

The forecasting system uses **park-specific models**.

Each park has its own model trained on that park’s historical visitation patterns.

---

## Stage 1 — Time-Series Forecast

A **Prophet model** generates baseline **monthly visitation forecasts** for each park.

This stage captures:

* seasonal visitation cycles
* long-term visitation trends
* annual park-specific patterns

---

## Stage 2 — Machine Learning Adjustment

An **XGBoost model** adjusts the baseline forecast using additional signals.

Features include:

* Google Trends search interest
* Social Media Exposure index
* weather anomalies
* holiday proximity
* lagged visitation

---

## Stage 3 — Weekly Disaggregation

Monthly forecasts are converted to weekly predictions using seasonal allocation factors.

The final output is a **26-week visitation forecast**.

---

# 13. Data Tables

## parks

```
park_id
park_name
latitude
longitude
state
region
accessibility_score
primary_airport
nearest_city
avg_annual_visits
```

---

## park_visitation_history

```
park_id
date
visits
temperature
precipitation
google_trends_index
sme_index
holiday_flag
```

---

## park_visitation_forecast

```
park_id
week_start_date
predicted_visits
crowd_score
weather_score
accessibility_score
trip_score
```

---

## crowd_calendar

```
park_id
week_start
crowd_score
weather_score
trip_score
color_code
```

---

## park_alerts

```
park_id
alert_type
severity
message
start_date
end_date
source
```

---

# 14. Non-Functional Requirements

* Page load < **2 seconds**
* Cached forecast responses
* No personal data collection

---

# 15. Out of Scope (V1)

* Mobile app
* Live traffic predictions
* Real-time parking availability
* Ranger operations dashboards

