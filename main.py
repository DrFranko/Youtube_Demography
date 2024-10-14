import streamlit as st
import pandas as pd
import plotly.express as px
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import pickle

# Load environment variables
load_dotenv()

# Set up YouTube API client
api_key = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=api_key)

# OAuth2 setup
CLIENT_SECRETS_FILE = os.getenv('CLIENT_SECRETS_FILE')
SCOPES = ['https://www.googleapis.com/auth/yt-analytics.readonly']
API_SERVICE_NAME = 'youtubeAnalytics'
API_VERSION = 'v2'

@st.cache_data
def get_channel_stats(channel_id):
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id
    )
    response = request.execute()

    return response['items'][0]

@st.cache_data
def get_video_stats(playlist_id):
    videos = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_id = item['contentDetails']['videoId']
            video_request = youtube.videos().list(
                part="snippet,statistics",
                id=video_id
            )
            video_response = video_request.execute()

            video_stats = video_response['items'][0]['statistics']
            video_stats['title'] = item['snippet']['title']
            video_stats['published_at'] = item['snippet']['publishedAt']
            videos.append(video_stats)

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return videos

def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_audience_geography(channel_id, credentials):
    youtube_analytics = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    request = youtube_analytics.reports().query(
        ids=f'channel=={channel_id}',
        startDate=start_date,
        endDate=end_date,
        metrics='views',
        dimensions='country',
        sort='-views'
    )
    response = request.execute()
    
    return response.get('rows', [])

def main():
    st.title("YouTube Channel Analysis")
    
    channel_id = st.text_input("Enter YouTube Channel ID")
    
    if channel_id:
        channel_stats = get_channel_stats(channel_id)
        
        st.header("Channel Statistics")
        st.write(f"Channel Name: {channel_stats['snippet']['title']}")
        st.write(f"Subscribers: {channel_stats['statistics']['subscriberCount']}")
        st.write(f"Total Views: {channel_stats['statistics']['viewCount']}")
        st.write(f"Total Videos: {channel_stats['statistics']['videoCount']}")
        
        uploads_playlist_id = channel_stats['contentDetails']['relatedPlaylists']['uploads']
        videos = get_video_stats(uploads_playlist_id)

        df = pd.DataFrame(videos)
        df['published_at'] = pd.to_datetime(df['published_at'])
        df['viewCount'] = pd.to_numeric(df['viewCount'])
        df['likeCount'] = pd.to_numeric(df['likeCount'])
        df['commentCount'] = pd.to_numeric(df['commentCount'])

        st.header("Video Performance Over Time")
        fig = px.scatter(df, x='published_at', y='viewCount', hover_data=['title'], title='Views per Video Over Time')
        st.plotly_chart(fig)

        st.header("Top 10 Most Viewed Videos")
        top_videos = df.nlargest(10, 'viewCount')
        st.table(top_videos[['title', 'viewCount', 'likeCount', 'commentCount']])

        st.header("Engagement Analysis")
        df['likes_to_views_ratio'] = df['likeCount'] / df['viewCount']
        fig = px.scatter(df, x='viewCount', y='likeCount', hover_data=['title'], 
                         title='Likes vs Views', trendline="ols")
        st.plotly_chart(fig)

        st.header("Monthly Video Upload Frequency")
        df['year_month'] = df['published_at'].dt.to_period('M')
        monthly_uploads = df.groupby('year_month').size().reset_index(name='count')
        monthly_uploads['year_month'] = monthly_uploads['year_month'].astype(str)
        fig = px.bar(monthly_uploads, x='year_month', y='count', title='Videos Uploaded per Month')
        st.plotly_chart(fig)
        
        st.header("Audience Geography")
        if st.button("Fetch Audience Geography"):
            with st.spinner("Authorizing and fetching data..."):
                try:
                    credentials = get_credentials()
                    geography_data = get_audience_geography(channel_id, credentials)
                    
                    if geography_data:
                        geo_df = pd.DataFrame(geography_data, columns=['Country', 'Views'])
                        geo_df['Views'] = pd.to_numeric(geo_df['Views'])
                        
                        fig = px.choropleth(geo_df, locations='Country', locationmode='country names', 
                                            color='Views', hover_name='Country', 
                                            title='Viewer Distribution by Country')
                        st.plotly_chart(fig)
                        
                        st.subheader("Top 10 Countries by Views")
                        st.table(geo_df.head(10))
                    else:
                        st.warning("No geography data available for this channel.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()