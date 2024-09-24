# YouTube Video Monitoring Tool to check for videos seen on your laptop by using browser history esp. by kids in parents absence

## Overview

This project is a Python application that retrieves the latest YouTube video links from your browser history, fetches their transcripts, and summarizes the content into concise summaries. This is specially built to monitor
kids who watches videos in parents absence. This application helps to get the videos seen by kids and provide a summary of them for quick review by parents.

This is a work in progress, as I am yet to add mailing functionality or streamlit app to generate summary on screen. As of now, it fetches latest 5 videos only, but count of videos can be easily changed in the sql written in python file.
query = "SELECT url, title FROM urls WHERE url like '%youtube.com/watch%' OR url like '%youtube.com/shorts%' ORDER BY last_visit_time DESC LIMIT 5" --change here to get number of latest videos

## Features

- **Fetch Latest YouTube Videos**: Automatically retrieves the most recently viewed YouTube videos from your browser history.
- **Transcription**: Uses the `YoutubeLoader` to extract video transcripts in manageable chunks.
- **Summarization**: Leverages advanced language models to summarize transcripts into 2-3 sentence summaries.
- **Environment Variable Support**: Utilizes environment variables for configuration, such as specifying the path to the browser history file.

## Requirements

- Python 3.x
- Required Python packages:
  - `langchain_community`
  - `langchain_groq`
  - `python-dotenv`
  - `sqlite3`
