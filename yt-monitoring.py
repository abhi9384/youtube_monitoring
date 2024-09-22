import sqlite3
import os
import shutil
import tempfile
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders.youtube import TranscriptFormat
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

def get_video_transcript(video_url):
    loader = YoutubeLoader.from_youtube_url(
        video_url,
        add_video_info=True,
        transcript_format=TranscriptFormat.CHUNKS,
        chunk_size_seconds=30,
    )

    full_text = loader.load()
    #print(full_text)

    video_transcript = [doc.page_content for doc in full_text]
    return video_transcript

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

def get_browser_history():
    history_file_url = os.getenv("history_file_url")
    #print('history_file_url: ', history_file_url)
    # Path to the browser history file
    history_path = os.path.expanduser(history_file_url)
    #print("history_path: ", history_path)
    #print('tempfile.gettempdir(): ', tempfile.gettempdir())
    # Copy the history file to a temporary location because it is locked while Chrome is running
    temp_history_path = os.path.join(tempfile.gettempdir(), 'History')
    shutil.copy2(history_path, temp_history_path)
    
    # Connect to the SQLite database
    conn = sqlite3.connect(temp_history_path)
    cursor = conn.cursor()
    
    # Query to retrieve URLs
    query = "SELECT url, title FROM urls WHERE url like '%youtube.com/watch%' OR url like '%youtube.com/shorts%' ORDER BY last_visit_time DESC LIMIT 5"
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

    #TODO add try catch block
    for row in rows:
        yt_video_url = row[0] 
        yt_video_title = row[1]
        yt_video_transcript = get_video_transcript(yt_video_url)
        yt_video_summary = summarize_transcript(yt_video_transcript)
        
        print('\n\n')
        print('URL: ', yt_video_url)
        print('Title: ', yt_video_title)
        print('Transcript: ', yt_video_transcript)
        print('Video Summary: ', yt_video_summary)

    #TODO: https://github.com/langchain-ai/langchain/blob/master/libs/community/tests/unit_tests/tools/gmail/test_send.py

if __name__ == "__main__":
    get_browser_history()