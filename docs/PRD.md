# California National Park Visitation Planner

## Product Requirements Document (PRD)

Version: 1.2
Status: In Development
Target Release: 9 March 2026

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

Initial parks supported:

* Yosemite National Park
* Joshua Tree National Park
* Death Valley National Park
* Sequoia National Park
* Kings Canyon National Park

Future expansion:

* Lassen Volcanic National Park
* Channel Islands National Park
* Redwood National and State Parks
* Pinnacles National Park

---

# 3. Target Users

### Primary User

Traveler / Trip Planner

Typical question:

"When can I visit Yosemite with minimal crowds?"

User needs:

* predicted crowd levels
* recommended visit windows
* weather expectations
* accessibility information

---

# 4. Forecast Horizon

Forecasts are generated **weekly for the next 26 weeks (6 months).**

Historical NPS data is monthly, so the system uses:

1. monthly baseline forecasts
2. weekly disaggregation

---

# 5. Core Scoring Metrics

The system calculates four primary scores.

## Crowd Score

Range: **0–100**

Calculation:

crowd_score = percentile_rank(predicted_weekly_visits within park history)

Meaning:

0–30 = very low crowds
31–60 = moderate crowds
61–80 = busy
81–100 = extremely crowded

---

## Weather Score

Range: **0–100**

weather_score =
0.6 × temperature_comfort

* 0.4 × precipitation_factor

Temperature comfort:

55–75°F → 100
40–55°F → 75
75–85°F → 70
<40°F or >90°F → 40

Precipitation factor:

<10% → 100
10–30% → 80
30–60% → 50

> 60% → 20

---

## Accessibility Score

Range: **0–100**

accessibility_score =

0.4 × airport_access_score
0.3 × drive_access_score
0.2 × road_access_score
0.1 × seasonal_access_score

Reference cities:

* San Francisco
* Los Angeles
* San Diego
* Sacramento
* Fresno

Reference airports:

* LAX
* SFO
* SAN
* SMF
* FAT

Users can click **Accessibility Details** to view the breakdown.

---

## Trip Score

Trip Score represents the overall travel desirability of a week.

trip_score =

0.6 × (100 − crowd_score)
0.3 × weather_score
0.1 × accessibility_score

Higher trip score = better week to visit.

---

# 6. Best Weeks to Visit

For each park the system identifies the **top 5 recommended weeks in the next 26 weeks**.

Algorithm:

1. calculate trip score for each week
2. remove weeks with severe alerts
3. rank by trip score
4. return top 5

---

# 7. Hidden Gem Weeks

A hidden gem week is defined as:

crowd_score < 40
weather_score > 60

These weeks offer low crowds with favorable weather.

---

# 8. Crowd Calendar

Each park page includes a **26-week crowd calendar**.

Each week is color coded:

Green → low crowds
Yellow → moderate
Orange → busy
Red → extremely crowded

Hovering reveals:

* week range
* crowd score
* weather score
* trip score

---

# 9. Homepage Layout

The homepage includes:

### Featured Insight Cards

1. Best park to visit this week
2. Hidden gem week recommendation
3. Lowest crowd score in next 30 days

### Interactive Map

A California map with park markers.

Marker colors represent current week crowd levels.

---

# 10. Alerts

The system supports alerts for events such as:

* wildfires
* flooding
* park closures
* road closures
* extreme heat

Alert severity:

Yellow → caution
Orange → disruption
Red → avoid visiting

Red alerts remove a week from recommendations.

---

# 11. Data Sources

* National Park Service visitation dataset
* Google Trends
* weather APIs
* accessibility metadata
* manually curated alerts

---

# 12. Data Tables

parks

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

---

park_visitation_history

park_id
date
visits
temperature
precipitation
google_trends_index
sme_index
holiday_flag

---

park_visitation_forecast

park_id
week_start_date
predicted_visits
crowd_score
weather_score
accessibility_score
trip_score

---

crowd_calendar

park_id
week_start
crowd_score
weather_score
trip_score
color_code

---

park_alerts

park_id
alert_type
severity
message
start_date
end_date
source

---

# 13. Non-Functional Requirements

Page load < 2 seconds
Cached forecasts
No personal data collection

---

# 14. Out of Scope (V1)

Mobile app
Live traffic predictions
Park ranger dashboards
