# Media Coverage Analysis System

A comprehensive Full-Stack AI-powered platform designed to aggregate, analyze, filter, and structure global media coverage reports in real time. The system leverages external live APIs, high-throughput LLM architectures for clickbait protection, and persistent relational indexing.

---

## 🚀 Tech Stack

### Frontend (User Interface)
* **Framework:** React (Vite)
* **Styling:** Tailwind CSS (Modern Glassmorphism Design with Native Dark/Light toggle support)
* **State Management:** Hooks-driven responsive client architecture

### Backend (API & Orchestration Layer)
* **Micro-framework:** Python Flask
* **API Documentation:** Flasgger (OpenAPI/Swagger Interactive Sandbox)
* **Security Cross-Origin:** Flask-CORS

### Data & Intelligence Layer
* **Persistent Relational Database:** SQLite 3 (Embedded Engine)
* **External Aggregator:** NewsAPI (Advanced Search Endpoint Engine)
* **LLM Engine:** Google Gemini AI (`gemini-2.5-flash` for high-speed analysis and summarization)

---

## 🏗️ System Architecture & Workflow

The platform utilizes a hybrid architectural ecosystem data-flow:
1. **Live Web Search (Client Loop):** The end-user enters keywords in the React interface. Flask fetches a targeted payload from NewsAPI, processes descriptions using the Gemini AI client to generate high-value summaries, and returns structured data back to the browser while immediately caching transaction footprints into the SQLite relational framework.
2. **Data Ingestion Engine (CLI Administrator Loop):** Administrators can execute high-volume data harvesting directly from the local terminal. The ingestion script pulls a larger batch of articles from the web, executes strict AI integrity evaluation to drop clickbait, and directly commits approved references straight into the SQLite tables.
3. **Data Sync Architecture:** Both the web frontend dashboards and backend analytical metrics are connected seamlessly to the single internal `database/app.db` storage.

---

## 🛠️ Implemented Features

* **Dashboard View:** Live keyword querying engine, streaming, and loading animations that safely intercept external API structures and render reactive cards containing AI analytics.
* **System Analytics Tab:** Real-time database monitoring dashboard showcasing direct synchronization metrics (Total SQLite Searches, Gemini Filtered Sources) and live connection heartbeat statuses.
* **Data & AI Ecosystem Tab:** Structured infrastructure summaries paired with a dynamic CLI execution history widget reading directly from raw database logs.
* **Robust Error Layer:** Centralized global exception routing built with full cross-origin resource handling to isolate runtime issues seamlessly.

---

## 📦 Getting Started & Execution Order

To spin up the entire Full-Stack ecosystem locally, execute commands in the exact sequence outlined below.

### 1. Clone the Repository
Open your terminal and clone the project, then navigate straight into the root directory:
```bash
git clone https://github.com/troki123/Media-coverage.git
cd Media-coverage
```

### 2. Environment Configuration Setup
Create a .env file inside the root folder (Media-coverage/). It must contain your valid API credentials to successfully route external cloud requests:

```env
NEWS_API_KEY=your_actual_news_api_key_here
GOOGLE_API_KEY=your_actual_gemini_api_key_here
```

### 3. Backend Setup & Execution (Python Flask)
Open a new terminal session in your IDE and run the following commands to create the virtual environment, link the interpreter, and install requirements:

#### Create the isolated Python virtual environment
```bash
python -m venv venv
```
#### Activate the virtual environment (Windows)
```bash
.\venv\Scripts\activate
```
#### Activate the virtual environment (macOS/Linux alternative)
```bash
source venv/bin/activate
```
#### Install all backend dependencies

VS Code Tip: Press Ctrl + Shift + P (or Cmd + Shift + P on Mac), search for "Python: Select Interpreter", and choose the interpreter inside your local (venv).
You might have to restart VS Code.

```bash
pip install -r requirements.txt
```

Now, launch the Flask backend server:
```bash
python main.py
```
### 4. Frontend Setup & Execution (React + Vite)
Open a separate, second terminal window to boot up the user interface. Install node packages, and launch the development pipeline:

#### Install UI packages
```bash
npm install
```
#### Run the frontend development server
```bash
npm run dev
```
### 5. Running the Test Suite
To verify core endpoint routing, strict AI clickbait filtering rules, and database integrity operations without spending API tokens, trigger the automated Pytest suite in your backend terminal:

```bash
pytest tests\test_main.py -v
```
