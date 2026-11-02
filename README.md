# 🛡️ Job Scam Detector

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ROSHINI075/job-scam-detector)

An AI and NLP-powered Flask web application designed to detect fraudulent job offers and scams, parse resumes for role suitability, and provide career safety insights.

---

## 🚀 How to View & Run the Web Application

### Option 1: 🌐 Run Instantly Online (GitHub Codespaces - Zero Installation)
You can launch and view the full interactive web application directly inside your browser without installing anything on your computer:

1. Click the **[Open in GitHub Codespaces](https://codespaces.new/ROSHINI075/job-scam-detector)** button above (or click **Code** > **Codespaces** > **Create codespace on main**).
2. GitHub will automatically set up the Python environment and install dependencies.
3. In the terminal inside Codespaces, start the application:
   `ash
   python app.py
   `
4. A popup notification will appear in the bottom right corner: **"Open in Browser"**. Click it to view and use the live application!

---

### Option 2: 💻 Run Locally on Your Computer

1. **Clone the repository:**
   `ash
   git clone https://github.com/ROSHINI075/job-scam-detector.git
   cd job-scam-detector
   `

2. **Create and activate a virtual environment:**
   `ash
   # Windows:
   python -m venv venv
   .\venv\Scripts\activate

   # macOS / Linux:
   python3 -m venv venv
   source venv/bin/activate
   `

3. **Install dependencies:**
   `ash
   pip install -r requirements.txt
   `

4. **Run the app:**
   `ash
   python app.py
   `

5. **Open in your browser:**
   Go to [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

### Option 3: ☁️ Deploy Free to the Cloud (Render / Railway)

To keep the website running 24/7 on a public .onrender.com link:

1. Go to [Render.com](https://render.com) and sign in with GitHub.
2. Click **New +** > **Web Service**.
3. Select your repository: ROSHINI075/job-scam-detector.
4. Set the following:
   - **Environment:** Python 3
   - **Build Command:** pip install -r requirements.txt
   - **Start Command:** python app.py
5. Click **Deploy Web Service**. Render will generate a free public HTTPS web address.

---

## ✨ Features
- **Job Scam Detection:** Scans job postings and descriptions for high-risk flags, suspicious salary promises, fee demands, and illegitimate contact methods.
- **Image OCR Support:** Extracts text from job flyers and screenshots using OCR.
- **Resume Skill Matcher:** Analyzes uploaded resumes against specific target job roles and highlights matching/missing skills.
- **AI Career Safety Assistant:** Built-in guidance chatbot for identifying employment fraud.
