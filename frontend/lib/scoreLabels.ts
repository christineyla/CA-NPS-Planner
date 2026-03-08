interface ForecastScoreSlice {
  crowd_score: number;
  weather_score: number;
  trip_score: number;
}

export function getCrowdScoreLabel(score: number): string {
  if (score <= 30) {
    return "Very quiet";
  }

  if (score <= 60) {
    return "Moderate visitation";
  }

  if (score <= 80) {
    return "Busy";
  }

  return "Peak congestion likely";
}

export function getWeatherScoreLabel(score: number): string {
  if (score >= 90) {
    return "Mild and dry";
  }

  if (score >= 75) {
    return "Pleasant overall";
  }

  if (score >= 60) {
    return "Warm with some variability";
  }

  if (score >= 45) {
    return "Cool with some precipitation";
  }

  return "Very hot or wet conditions";
}

export function getTripScoreLabel(score: number): string {
  if (score >= 85) {
    return "Excellent visit window";
  }

  if (score >= 70) {
    return "Strong option";
  }

  if (score >= 55) {
    return "Worth considering";
  }

  if (score >= 40) {
    return "Mixed conditions";
  }

  return "Challenging timing";
}

export function getScoreCardLabels(scores: ForecastScoreSlice) {
  return {
    crowd: getCrowdScoreLabel(scores.crowd_score),
    weather: getWeatherScoreLabel(scores.weather_score),
    trip: getTripScoreLabel(scores.trip_score),
  };
}
