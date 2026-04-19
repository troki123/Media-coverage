#News Search & Database Storage (news-search branch)
This part of the project focuses on news retrieval and data storage. Instead of just dumping links into the terminal, I've implemented a system that cleans the data and saves it locally so we don't lose our research results once the session ends.

##What’s New?
*Noise Filtering: I configured the search logic to automatically block "noisy" domains (YouTube, Reddit, Instagram, TikTok, etc.). The goal was to ensure we only process actual news portals and official websites.

*AI Refinement: Gemini 2.5 Flash acts as a final filter here. It doesn't write summaries in this step; instead, it double-checks the link quality and formats the output into a "pipe-separated" string (Title | Link) so Python can easily parse it for the database.

*Local Storage: I changed the SQLite database. Now, every search session is saved with a unique ID (based on a timestamp). This allows us to track exactly which links were found in which specific search batch.

##How the Code is Organized
*init_db.py: It automatically creates the database folder and the media_news table if they don't exist. You can run it once or let app.py handle it automatically.

*app.py: The core logic. This is where the Tavily search, AI filtering, and the final database commit all come together.

*.gitignore: Very important—I added the .db files to the ignore list. This prevents us from pushing local database changes to GitHub, keeping the repo clean while keeping the data private on our own machines.

##How to Run It
Make sure your API keys are set in the .env file (GOOGLE_API_KEY and TAVILY_API_KEY).

Install dependencies (if you haven't already): pip install -r requirements.txt.

Run the application:

Bash
python app.py
Enter your topic, and the filtered links will be saved automatically to database/app.db.

##Checking the Data
If you want to see what's been saved, the easiest way is to install the SQLite Viewer extension in VS Code. Once installed, just click on the app.db file to see the table with titles, URLs, and their corresponding Search IDs.