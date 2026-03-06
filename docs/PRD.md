# California National Park Visitation Planner

## Product Requirements Document (PRD)

Version: **1.4**  
Status: In Development  
Target Release: **9 March 2026**

---

# 1. Executive Summary

The **California National Park Visitation Planner** transforms public data into actionable travel insights.

By combining:

- historical visitation data
- search trends
- weather forecasts
- accessibility information
- seasonal alerts

the system predicts crowd levels at California national parks and recommends optimal travel windows.

The platform converts complex forecasts into simple travel guidance, helping visitors plan trips with lower congestion and better conditions.

---

# 2. Parks in Scope

## Initial parks supported

- Yosemite National Park  
- Joshua Tree National Park  
- Death Valley National Park  
- Sequoia National Park  
- Kings Canyon National Park  

## Future expansion

- Lassen Volcanic National Park  
- Channel Islands National Park  
- Redwood National and State Parks  
- Pinnacles National Park  

---

# 3. Target Users

## Primary User

Traveler / Trip Planner

Typical question:

> “When can I visit Yosemite with minimal crowds?”

## User Needs

- predicted crowd levels
- recommended visit windows
- weather expectations
- accessibility information

---

# 4. Forecast Horizon

Forecasts are generated **weekly for the next 26 weeks (6 months).**

Because historical NPS visitation data is monthly, the system uses:

1. **monthly baseline forecasts**
2. **weekly disaggregation**

---

# 5. Historical Data Window

To simplify ETL pipelines and improve data reliability, the forecasting system trains on the most recent **3 years of historical data**.

This window provides sufficient seasonal signal while keeping ingestion pipelines lightweight during early system development.

Future versions may expand this window to **5–10 years** once the pipeline is stable.

### Visitation Data

- Monthly NPS visitation data  
- Approximately **last 3 years**

### Weather Data

- Historical temperature and precipitation observations  
- Approximately **last 3 years**

### Trend Signals

Optional signals used to adjust forecasts:

- Google Trends search interest  
- Social Media Exposure Index (SME)

### Data Exceptions

Disruption periods such as **pandemic-era visitation (2020–2021)** may be:

- flagged as anomalies  
- downweighted during model training

---

# 6. Core Scoring Metrics

The system calculates four primary scores.

---

## Crowd Score

Range: **0–100**

Calculation:

```
crowd_score = percentile_rank(predicted_weekly_visits within park history)
```

Meaning:

| Score | Interpretation |
|------|---------------|
| 0–30 | Very low crowds |
| 31–60 | Moderate crowds |
| 61–80 | Busy |
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

| Temperature | Score |
|-------------|------|
| 55–75°F | 100 |
| 40–55°F | 75 |
| 75–85°F | 70 |
| <40°F or >90°F | 40 |

### Precipitation Factor

| Chance of precipitation | Score |
|------------------------|------|
| <10% | 100 |
| 10–30% | 80 |
| 30–60% | 50 |
| >60% | 20 |

### Weather Forecast Strategy

Because long-range weather forecasts are uncertain:

- Short-range forecasts use actual weather prediction data.
- Longer horizon weeks use **seasonal weather expectations derived from historical averages**.

The weather score reflects **expected comfort conditions rather than exact future weather**.

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

- San Francisco  
- Los Angeles  
- San Diego  
- Sacramento  
- Fresno  

### Reference Airports

- LAX  
- SFO  
- SAN  
- SMF  
- FAT  

Users can click **Accessibility Details** to view interpretable travel details including:

- nearest airport
- distance to airport
- nearest city
- drive time estimates
- road access notes
- seasonal access considerations

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

# 7. Best Weeks to Visit

For each park the system identifies the **top 5 recommended weeks in the next 26 weeks**.

Algorithm:

1. calculate trip score for each week
2. remove weeks with **severe alerts**
3. rank by trip score
4. return top 5

---

# 8. Hidden Gem Weeks

A hidden gem week is defined as:

```
crowd_score < 40
weather_score > 60
```

These weeks offer **low crowds with favorable weather**.

---

# 9. Crowd Calendar

Each park page includes a **6-month crowd calendar**.

Calendar structure:

- months displayed **horizontally**
- weeks stacked **vertically under each month**

Weeks are color coded:

| Color | Crowd Level |
|------|-------------|
| Green | Low crowds |
| Yellow | Moderate |
| Orange | Busy |
| Red | Extremely crowded |

Hovering reveals:

- week range
- crowd score
- weather score
- trip score

---

# 10. Homepage Layout

The homepage contains two primary sections.

## Exploration Section

- Featured insight cards
- California National Park Crowd Score map

### Featured Insight Cards

- Best park to visit this week
- Lowest crowd score in next 30 days
- Best weather score in next 30 days

### Interactive Map

A California map with park markers.

Marker colors represent **current week crowd levels**.

Clicking a park marker updates the **selected park analytics panel** on the homepage.

---

## Analytics Section

Displays analytics for the selected park including:

- score cards
- visitation forecast chart
- best weeks
- hidden gem weeks
- crowd calendar
- alerts
- accessibility details

---

# 11. Alerts

The system supports alerts for events such as:

- wildfires
- flooding
- park closures
- road closures
- extreme heat

### Alert Severity

| Level | Meaning |
|------|--------|
| Yellow | Caution |
| Orange | Disruption |
| Red | Avoid visiting |

Red alerts **remove affected weeks from recommendations**.

---

## Alert Categories

| Alert Type | Example Event |
|------------|--------------|
| Wildfire | wildfire closure or smoke hazard |
| Extreme Heat | dangerous heat advisory |
| Flooding | road flooding or storm damage |
| Road Closure | highway or access road closure |
| Park Closure | park or area temporarily closed |

---

# 12. Data Sources

The system aggregates data from multiple public sources.

### National Park Service

- historical visitation dataset

### Search Trends

- Google Trends search interest

### Weather

- historical observations
- short-range forecasts
- seasonal averages

### Accessibility Metadata

- airport proximity
- drive time estimates
- seasonal access constraints

### Social Media Exposure Index (SME)

SME captures online popularity signals.

Sources may include:

- Google Trends search frequency
- social media hashtag volume
- media mentions

Values are normalized to **0–100**.

---

# 13. Forecast Model Architecture

The forecasting system uses **park-specific models**.

Each park has its own model trained on that park’s historical visitation patterns.

## Stage 1 — Time Series Forecast

A **Prophet model** generates baseline **monthly visitation forecasts**.

Captures:

- seasonal cycles
- long-term trends
- park-specific visitation patterns

## Stage 2 — Machine Learning Adjustment

An **XGBoost model** adjusts the baseline forecast.

Features include:

- Google Trends search interest
- Social Media Exposure index
- weather anomalies
- holiday proximity
- lagged visitation

## Stage 3 — Weekly Disaggregation

Monthly forecasts are converted to weekly predictions using seasonal allocation factors.

Output is a **26-week forecast**.

---

# 14. Data Freshness & Metadata

To support reproducibility and debugging, the system stores metadata timestamps with ingested and generated data.

Tracked timestamps include:

| Field | Purpose |
|------|--------|
| ingested_at | when a record was loaded into the system |
| source_updated_at | last update time from the original source |
| forecast_generated_at | when the forecast was produced |
| model_trained_at | when the model was last trained |
| data_cutoff_date | latest historical data used for forecast |
| last_verified_at | last review time for alerts |

These fields enable:

- pipeline monitoring
- forecast reproducibility
- stale data detection
- ETL debugging

---

# 15. Data Tables

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
data_source
source_updated_at
ingested_at
```

## park_visitation_forecast

```
park_id
week_start_date
predicted_visits
crowd_score
weather_score
accessibility_score
trip_score
forecast_generated_at
model_trained_at
data_cutoff_date
model_version
```

## crowd_calendar

```
park_id
week_start
crowd_score
weather_score
trip_score
color_code
```

## park_alerts

```
park_id
alert_type
severity
message
start_date
end_date
source
ingested_at
last_verified_at
```

---

# 16. Non-Functional Requirements

- Page load < **2 seconds**
- Cached forecast responses
- No personal data collection

---

# 17. Out of Scope (V1)

- Mobile app
- Live traffic predictions
- Real-time parking availability
- Ranger operations dashboards
