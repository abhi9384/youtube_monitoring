# YouTube Video Monitoring Tool to check for videos seen on your laptop by using browser history esp. by kids in parents absence

## Overview

This project is a Python application that retrieves the latest YouTube video links from your browser history, fetches their transcripts, and summarizes the content into concise summaries. This is specially built to monitor kids who watches videos in parents absence. This application helps to get the videos seen by kids and provide a summary of them for quick review by parents.

It fetches last 1 day videos only, but can be easily changed in the sql written in python file.
query = "SELECT url, title, 
                strftime('%Y-%m-%d %H:%M:%S', (last_visit_time / 1000000) - 11644473600, 'unixepoch') AS last_visit_time
                FROM urls 
                WHERE url like '%youtube.com/watch%' OR url like '%youtube.com/shorts%' 
                AND last_visit_time >= (strftime('%s', 'now', '-1 day') * 1000000) + 11644473600000000
                ORDER BY last_visit_time DESCS"


## Features
- **YouTube Video Analysis**: Fetches and analyzes recent YouTube videos from browser history.
- **Transcript Extraction**: Extracts video transcripts (limited to the first 2 minutes) from YouTube videos using the YouTube Transcript API.
- **Summarization**: Summarizes the extracted transcript into 2-3 sentences.
- **Content Suitability Check**: Analyzes whether the video is safe for children under 10 years based on the transcript summary.
- **Streamlit UI**: A user-friendly interface built with Streamlit to interact with the app.

- It can be easily extended to see all websites visited recently by modifying the sql query in the python file

## Requirements

- Python 3.x
- Streamlit
- langchain_groq
- youtube_transcript_api
- python-dotenv
- sqlite3 (built-in)
- shutil, tempfile (built-in)
- dotenv (for environment variable loading)