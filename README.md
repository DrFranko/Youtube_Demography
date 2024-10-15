# YouTube Channel Analysis

## Overview
This Streamlit application allows users to analyze YouTube channel statistics, including video performance, audience geography, and engagement metrics. The app utilizes the YouTube Data API and YouTube Analytics API to fetch real-time data for a specified YouTube channel.

## Features
- **Channel Statistics**: Display basic information about the channel, such as name, subscriber count, total views, and total videos.
- **Video Performance Over Time**: Visualize views per video over time using scatter plots.
- **Top Viewed Videos**: Show a table of the top 10 most viewed videos with their corresponding metrics.
- **Engagement Analysis**: Analyze the relationship between likes and views.
- **Monthly Video Upload Frequency**: Display the frequency of video uploads on a monthly basis.
- **Audience Geography**: Visualize the distribution of viewers by country using a choropleth map.

## Prerequisites
- Python 3.6 or higher
- Streamlit
- Pandas
- Plotly
- Google API Client
- Google OAuth2 Credentials
- A `.env` file containing your YouTube API key and client secrets file

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/DrFranko/Youtube_Demography.git

2. Create a .env file:
   -YOUTUBE_API_KEY=your_youtube_api_key
   -CLIENT_SECRETS_FILE=path_to_your_client_secrets.json
