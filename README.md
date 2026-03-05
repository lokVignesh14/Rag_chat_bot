# 🤖 RAG AI Chatbot
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-green)
![Streamlit](https://img.shields.io/badge/frontend-Streamlit-red)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

An intelligent **Retrieval-Augmented Generation (RAG) chatbot** built using modern AI technologies.  
This project enables users to interact with a knowledge base through natural language and receive accurate responses supported by retrieved information.

The system combines **FastAPI APIs, Streamlit UI, vector search, and LLM reasoning** to deliver a responsive conversational assistant.

---

# ✨ Features

- **RAG Architecture** – Combines retrieval systems with LLMs for accurate responses  
- **AI Chat Interface** – Interactive chatbot for querying the knowledge base  
- **Vector Search** – Efficient document retrieval for contextual answers  
- **Voice Support** – Speech-to-text and text-to-speech capabilities  
- **Multi-language Responses** – Translate chatbot replies into multiple languages  
- **API Key Authentication** – Secure API access for backend endpoints  
- **Lead Capture System** – Optional form submission for user enquiries  
- **Image & Product Cards** – Supports structured responses with images

---

# 🚀 Quick Start

## Prerequisites

- Python >=3.10
- OpenAI API key
- Internet connection

---

# 📦 Installation

### 1 Clone the repository

```bash
git clone https://github.com/yourusername/rag-chatbot.git
cd rag-chatbot
```

### 2 Create Virtual Environment

```bash
python -m venv venv
```

Linux / Mac

```bash
source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

---

### 3 Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ⚙️ Configuration

Create a `.env` file in the project root.

```env
OPENAI_API_KEY=your_openai_api_key
BACKEND_URL=http://127.0.0.1:8000
```

---

# ▶️ Running the Project

### Start Backend Server

```bash
uvicorn main:app --reload
```

Backend will run at:

```
http://127.0.0.1:8000
```

---

### Start Streamlit Frontend

```bash
streamlit run streamlit_app.py
```

Frontend will run at:

```
http://localhost:8501
```

---

# 📂 Project Structure

```
rag-chatbot/
│
├── streamlit_app.py        # Streamlit frontend
├── main.py                 # FastAPI backend
├── requirements.txt        # Dependencies
├── .env                    # Environment variables
│
├── data/
│   └── knowledge_base.json # Knowledge base data
│
└── README.md
```

---

# 🎯 Use Cases

- **Customer Support Chatbot**
- **Internal Knowledge Base Assistant**
- **Product Information Bot**
- **Documentation Search Assistant**
- **Voice-enabled AI assistant**

---

# 🤝 Contributing

Contributions are welcome.

1. Fork the repository  
2. Create your feature branch  

```
git checkout -b feature/new-feature
```

3. Commit your changes  

```
git commit -m "Add new feature"
```

4. Push to the branch  

```
git push origin feature/new-feature
```

5. Open a Pull Request

---

# 📚 Resources

- https://fastapi.tiangolo.com
- https://streamlit.io
- https://platform.openai.com/docs

---

# 📝 License

This project is licensed under the MIT License.
