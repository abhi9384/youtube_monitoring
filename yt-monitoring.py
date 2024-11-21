import sqlite3
import os
import shutil
import tempfile
#from langchain_community.document_loaders import YoutubeLoader
#from langchain_community.document_loaders.youtube import TranscriptFormat
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_video_transcript(video_url):
    
    # loader = YoutubeLoader.from_youtube_url(
    #     video_url,
    #     add_video_info=False, #True
    #     transcript_format=TranscriptFormat.CHUNKS,
    #     chunk_size_seconds=30,
    # )

    # full_text = loader.load()
    
    # video_transcript = [doc.page_content for doc in full_text]

    #getting transcript only for first 2 mins, to make sure for longer videos, we are not passing too much data to LLM

    try:
        # Fetch the transcript
        video_id = video_url.split("v=")[-1]  # Get the video ID from the URL
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Extract transcript chunks for the first 2 minutes (120 seconds)
        first_2_minutes_transcript = [entry for entry in transcript if entry['start'] <= 120]

        # Format the transcript for readability
        formatted_video_transcript = [f"{entry['text']}" for entry in first_2_minutes_transcript]
    except Exception as e:
        #st.error(f"An error occurred for url yt_video_url: {e}")
        formatted_video_transcript = ""

    return formatted_video_transcript

def summarize_transcript(video_transcript):

    model = ChatGroq(model="mixtral-8x7b-32768")

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant, who is expert in summarizing text in 2 to 3 sentences"),
            ("human", "Summarize the {yt_transcript} into maximum 2 to 3 sentences")
        ]
    )

    chain = prompt_template | model | StrOutputParser()

    summary_transcript = chain.invoke({"yt_transcript": video_transcript})
    return summary_transcript

def check_video_suitability(summarized_transcript):

    model = ChatGroq(model="mixtral-8x7b-32768", temperature=0.0)

    prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", f"""
            You are a helpful assistant with expertise in analyzing text for content appropriateness. Your task is to assess whether the provided text contains any of the following:
            - Obscene or explicit language
            - Racist content
            - Violent themes
            - Provocative or inappropriate content

            If the text does not contain any of these elements and is suitable for children under 10 years old, respond with: 'Safe'.
            If the text contains any of the elements above, respond with: 'Unsafe'.
            Your response should only be one word, either 'Safe' or 'Unsafe'. Please display only the appropriate response and nothing else.

            Note: Topics like career discussions, achievements in sports (e.g., wrestling), and general commentary are considered safe unless they involve explicit content.
        """),
        ("human", f"""
            Analyze this text. Text is {summarized_transcript}
        """)
        ]
        )

    chain = prompt_template | model | StrOutputParser()

    transcript_checker = chain.invoke({"summarized_transcript": summarized_transcript})
    return transcript_checker

def get_browser_history():
    history_file_url = os.getenv("ms_edge_history_file_url")
    # Path to the browser history file
    history_path = os.path.expanduser(history_file_url)
    # Copy the history file to a temporary location because it is locked while Chrome is running
    temp_history_path = os.path.join(tempfile.gettempdir(), 'History')
    shutil.copy2(history_path, temp_history_path)
    
    # Connect to the SQLite database
    conn = sqlite3.connect(temp_history_path)
    cursor = conn.cursor()
    
    # Query to retrieve URLs for last 1 day
    query = f"""SELECT url, title, 
                strftime('%Y-%m-%d %H:%M:%S', (last_visit_time / 1000000) - 11644473600, 'unixepoch') AS last_visit_time
                FROM urls 
                WHERE url like '%youtube.com/watch%' OR url like '%youtube.com/shorts%' 
                AND last_visit_time >= (strftime('%s', 'now', '-1 day') * 1000000) + 11644473600000000
                ORDER BY last_visit_time DESC LIMIT 5"""        # using limit to restrict number of videos in dev
    #query = "SELECT sql FROM sqlite_schema WHERE name = 'urls'"
    #CREATE TABLE urls(id INTEGER PRIMARY KEY AUTOINCREMENT,url LONGVARCHAR,title LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT NULL,typed_count INTEGER DEFAULT 0 NOT NULL,last_visit_time INTEGER NOT NULL,hidden INTEGER DEFAULT 0 NOT NULL)
    cursor.execute(query)
    
    # Fetch and print the results
    #sql = cursor.fetchone()[0]
    #print(sql)
    rows = cursor.fetchall()
    # Clean up
    conn.close()
    os.remove(temp_history_path)

    return rows

def app():

    # Streamlit app UI
    st.set_page_config(page_title="YouTube Watch History Tracker", layout="wide")

    # Title and description
    st.title("📺 YouTube Watch History Tracker for Kids")
    st.markdown(
        """
        This app allows you to analyze the YouTube videos watched by kids by reading the browser history. 
        Click on the button and the app will generate a summary of the most recent videos watched.
        """
    )

    # Add custom styling
    st.markdown("""
        <style>
        .main-title {
            font-size: 36px;
            font-weight: bold;
            color: #2C3E50;
            text-align: center;
        }
        .desc {
            font-size: 18px;
            text-align: center;
            margin-bottom: 30px;
        }
        .button {
            background-color: #2980B9;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 5px;
        }
        .button:hover {
            background-color: #1ABC9C;
        }
        .video-card {
            padding: 20px;
            border-radius: 8px;
            background-color: #ECF0F1;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        .video-card-title {
            font-size: 18px;
            font-weight: bold;
            color: #34495E;
        }
        .video-card-summary {
            font-size: 14px;
            color: #7F8C8D;
        }
        </style>
    """, unsafe_allow_html=True)

    if 'button_disabled' not in st.session_state:
        st.session_state.button_disabled = False

    if st.button("Analyze Videos", disabled=st.session_state.button_disabled):
        
        # Disable the button when the spinner starts
        st.session_state.button_disabled = True

        try:
            with st.spinner("**Processing browser history... Please wait**"):
                
                rows = get_browser_history()

                if len(rows) == 0:
                    st.warning("No YouTube videos found in the history.")

                else:
                    # Create containers to display each video summary in cards
                    with st.container():
                        for row in rows:
                            try:
                                yt_video_url = row[0] 
                                yt_video_title = row[1]
                                yt_video_watched_at = row[2]
                                yt_video_transcript = get_video_transcript(yt_video_url)
                                if len(yt_video_transcript) > 0: 
                                    yt_video_summary = summarize_transcript(yt_video_transcript)
                                    transcript_suitability_checker = check_video_suitability(yt_video_summary)
                                else:
                                    yt_video_summary = "Sorry, could not extract transcript for this video"  
                                    transcript_suitability_checker = "Sorry, could not extract transcript for this video"  
                                
                                # Display the results
                                st.subheader(f"Video: {yt_video_title}")
                                st.write(f"**URL**: {yt_video_url}")
                                st.write(f"**Video watched at**: {yt_video_watched_at}")
                                st.write(f"**Transcript Summary**: {yt_video_summary}")
                                if transcript_suitability_checker.startswith("Unsafe"):
                                    st.write(f"**Is Video suitable for kids**: <span style='color:red;'>{transcript_suitability_checker}</span>", unsafe_allow_html=True)
                                elif transcript_suitability_checker.startswith("Safe"):
                                    st.write(f"**Is Video suitable for kids**: <span style='color:blue;'>{transcript_suitability_checker}</span>", unsafe_allow_html=True)    
                                else:
                                    st.write(f"**Is Video suitable for kids**: {transcript_suitability_checker}")    
                                st.write("---")

                            except Exception as e:
                                st.error(f"An error occurred for url yt_video_url: {e}")
            
        except Exception as e:
            st.error(f"An error while reading browser history: {e}")
        
        # Re-enable the button after the process finishes
        st.session_state.button_disabled = False
        st.success("Process Completed!")
    
    # Footer message
    st.markdown("Made with ❤️ by Your Team | Version 1.0")

if __name__ == "__main__":
    app()