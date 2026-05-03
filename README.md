# NastaliqScan

**An AI-powered dyslexia screening tool for Urdu and English writing**

NastaliqScan is an intelligent, accessible platform designed to help identify potential dyslexic patterns in children's writing through advanced AI analysis. Built with Streamlit and powered by Google Gemini 2.5 Flash, it provides real-time feedback on text and handwriting samples in both Urdu and English, with full right-to-left (RTL) language support.

---

## 🎯 Problem Statement

Dyslexia is a common learning disorder that affects approximately 5-10% of the population, including a significant portion of Pakistani children. However, early screening and intervention can dramatically improve educational outcomes. 

**Current Challenges:**
- Limited access to dyslexia screening tools in Pakistan
- Lack of localized screening solutions for Urdu language users
- Expensive professional assessments that are inaccessible to most families
- Few digital tools that support RTL languages like Urdu

NastaliqScan addresses these gaps by providing an **affordable, accessible, and AI-powered screening tool** that parents, educators, and health professionals can use to identify potential dyslexic writing patterns early on.

---

## ✨ Key Features

- **📝 Text Analysis Mode**: Submit written text for instant AI-powered analysis of dyslexic patterns including spelling, phonetic errors, and letter reversals

- **🖼️ Handwriting Image Upload**: Analyze photos of handwritten documents to detect handwriting-based dyslexic indicators

- **⚠️ Risk Level Assessment**: Get a clear risk classification (Low, Medium, High) with detailed explanations of identified patterns

- **🔤 Inline Urdu Error Highlighting**: Visual highlighting of specific errors directly in Urdu text with color-coded annotations

- **📄 Downloadable PDF Reports**: Generate comprehensive, professional PDF reports with analysis results, risk assessment, and recommendations

- **🌍 RTL Language Support**: Full support for Urdu and other right-to-left languages with proper text rendering and formatting

- **⚡ Real-time Processing**: Get results instantly using Google Gemini 2.5 Flash for fast, accurate AI analysis

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend/UI** | Streamlit |
| **AI Engine** | Google Gemini 2.5 Flash |
| **PDF Generation** | ReportLab |
| **Language** | Python 3.8+ |
| **Deployment** | Google Cloud Run |
| **Container** | Docker |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- A Google Cloud account with Gemini API access
- pip (Python package manager)

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/NastaliqScan.git
   cd NastaliqScan
   ```

2. **Create a `.env` file** in the project root with your Gemini API key:
   ```bash
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```
   
   To get your API key:
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key and copy it

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```
   
   The app will open in your default browser at `http://localhost:8501`

---

## ☁️ Deployment on Google Cloud Run

### Prerequisites

- Google Cloud SDK installed (`gcloud` CLI)
- Docker installed
- A Google Cloud project with Cloud Run enabled

### Deployment Steps

1. **Authenticate with Google Cloud**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Build and push Docker image**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/nastaliqscan
   ```

3. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy nastaliqscan \
     --image gcr.io/YOUR_PROJECT_ID/nastaliqscan \
     --platform managed \
     --region us-central1 \
     --set-env-vars GEMINI_API_KEY=your_api_key \
     --allow-unauthenticated
   ```

4. **Access your deployed app**
   - Cloud Run will provide a URL (e.g., `https://nastaliqscan-xxxxx.a.run.app`)
   - Your app is now live!

### Environment Variables for Cloud Run

Set these in the deployment command:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `PORT`: (optional) Default is 8080

---

## 📸 Screenshots

- **Main interface with text input mode**
  <img src="https://github.com/user-attachments/assets/c0099e8c-fcf5-4011-9cea-0cea772df7da" width="960" height="474" alt="Main interface">

- **Handwriting upload feature**
  <img src="https://github.com/user-attachments/assets/40332634-ffdd-4b74-a836-32d5f2d0799e" width="960" height="476" alt="Handwriting upload">

- **Risk assessment results with error highlighting**
  <img src="https://github.com/user-attachments/assets/cd5d79da-b2be-4221-9226-ce9993419689" width="960" height="474" alt="Risk assessment">

- **PDF report generation**
  <img src="https://github.com/user-attachments/assets/2172ca03-0b7c-49d9-9d9c-659d5b35fd6a" width="960" height="200" alt="PDF generation">

- **Mobile-responsive design**
  <img src="https://github.com/user-attachments/assets/a369f15f-6214-48f3-a5a9-35800fcbce61" width="350" height="428" alt="Mobile design">


---

## 📋 Usage Guide

### Analyzing Text

1. Navigate to the **"Text Analysis"** tab
2. Paste or type the writing sample (Urdu, English, or mixed)
3. Click **"Analyze"**
4. Review the risk assessment and identified patterns
5. Download the PDF report if needed

### Analyzing Handwriting

1. Navigate to the **"Handwriting Analysis"** tab
2. Upload a clear photo of the handwritten document
3. Wait for OCR and AI analysis to complete
4. Review results with visual highlighting of errors
5. Generate and download a comprehensive report

---

## ⚠️ Important Disclaimer

**NastaliqScan is NOT a medical diagnosis tool.** This application is designed to:
- Screen for potential dyslexic writing patterns
- Provide educational insights
- Support early identification in educational settings

**It is NOT intended to:**
- Provide medical diagnoses
- Replace professional dyslexia assessments
- Substitute for clinical psychologist evaluation
- Provide medical advice

Please consult qualified professionals (educational psychologists, speech-language pathologists, or dyslexia specialists) for formal diagnosis and treatment. Results from this tool should be used as a screening aid only, to inform further professional evaluation if needed.

---


---

## 🤝 Contributing

We welcome contributions! Please feel free to:
- Report bugs and issues
- Suggest new features
- Submit pull requests
- Improve documentation

---

## 📧 Contact & Support

For questions, feedback, or support, please contact:
- **Email**: [amnanoor0179@gmail.com]

---

## 🎓 Built for AI Seekho 2026 by Google Cloud Pakistan

This project was developed as part of the **AI Seekho 2026 initiative** by Google Cloud Pakistan, aimed at empowering Pakistani innovators to build AI-powered solutions that address local challenges and improve lives in underserved communities.

---

**NastaliqScan** - Making dyslexia screening accessible, affordable, and intelligent. 🌟
