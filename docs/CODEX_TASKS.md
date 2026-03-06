# Codex Task List

## California National Park Visitation Planner

This file defines the sequential tasks Codex should execute when building the application.

Codex should complete tasks **one at a time**, reviewing repository changes after each task.

---

# Task 1 — Project Scaffold

Create the initial monorepo scaffold for the California National Park Visitation Planner.

Repository structure:

frontend/
backend/
docs/
data/
scripts/

Frontend requirements:

* Next.js with TypeScript
* Tailwind CSS
* App Router architecture
* folders for components, lib, and types

Backend requirements:

* FastAPI project
* Python project structure
* folders for api, models, services, jobs, and tests
* requirements.txt

Developer environment:

* environment example files
* linting and formatting configuration
* README with setup instructions

Focus only on structure and developer experience.

---

# Task 2 — Database Models and Seed Data

Implement backend database models for:

parks
park_visitation_history
park_visitation_forecast
crowd_calendar
park_alerts

Seed mock data for the following parks:

* Yosemite National Park
* Joshua Tree National Park
* Death Valley National Park
* Sequoia National Park
* Kings Canyon National Park

Seed data should include:

* 26 weeks of forecast data
* accessibility scores
* example alerts

Add scripts to seed the database locally.

---

# Task 3 — Backend API Endpoints

Implement FastAPI routes:

GET /parks
GET /parks/map-data
GET /parks/{park_id}
GET /parks/{park_id}/forecast
GET /parks/{park_id}/best-weeks
GET /parks/{park_id}/calendar
GET /parks/{park_id}/accessibility
GET /parks/{park_id}/alerts

Use mock data for responses.

Add basic API tests.

---

# Task 4 — Homepage UI

Build the homepage using Next.js.

Homepage components:

* header
* featured insight cards
* California park map
* clickable park markers

Three featured cards:

* Best park to visit this week
* Hidden gem week recommendation
* Lowest crowd score in next 30 days

Map markers should represent the five parks.

---

# Task 5 — Park Dashboard

Create the park detail dashboard page.

Components include:

* park summary panel
* crowd score card
* weather score card
* trip score card
* historical + forecast chart
* best weeks list
* hidden gem badges
* crowd calendar (26 weeks)
* alert banner
* accessibility details modal

Dashboard should fetch mock API data.

---

# Task 6 — Scoring Logic

Implement backend scoring services for:

crowd score
weather score
accessibility score
trip score

Also implement:

hidden gem classification
best-week recommendation logic
alert suppression rules

Add unit tests.

---

# Task 7 — Forecast Pipeline

Implement forecasting pipeline modules:

* Prophet monthly forecast
* weekly disaggregation
* XGBoost adjustment layer

Add job pipelines for:

daily data ingestion
weekly retraining
daily forecast generation

Models may be mocked initially.

---

# Task 8 — Cache and Production Readiness

Add:

Redis caching for forecast endpoints
improved error handling
developer scripts
test commands

Ensure the project runs locally end-to-end.

Add final README instructions.
