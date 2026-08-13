# 🌐 LinguaFlow

**AI-Powered Multilingual Translation Platform**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://linguaflowtranslate.streamlit.app/)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?logo=github&logoColor=white)](https://github.com/nabinchettri18/CodeAlpha_LinguaFlow)

LinguaFlow is a resilient multilingual AI translation platform built with **Python, Streamlit, Google Gemini, NVIDIA Nemotron, SQLite, and automatic language detection**.

The core engineering idea is a **multi-provider fallback architecture**: Gemini 2.5 Flash handles primary translation, Gemini Flash-Lite provides a secondary fallback, and NVIDIA Nemotron 3 Ultra acts as the final reliability provider.

## 🚀 Live Demo

**Try LinguaFlow:** https://linguaflowtranslate.streamlit.app/

**Source Code:** https://github.com/nabinchettri18/CodeAlpha_LinguaFlow

> The hosted Streamlit deployment uses the Google GenAI Python SDK directly. Local development can use the Node.js Gemini service.

---

## ✨ Key Features

- 🌍 Multilingual AI translation
- 🔍 Automatic language detection
- ⚡ SQLite translation caching
- 🤖 Gemini 2.5 Flash primary provider
- 🔄 Gemini Flash-Lite secondary fallback
- 🛡️ NVIDIA Nemotron 3 Ultra final fallback
- ♻️ Retry, cooldown, and graceful provider failure handling
- ✅ Translation output validation
- 🧩 Streamlit web interface
- ☁️ Streamlit Cloud deployment
- 💻 Local Node.js Gemini service for development
- 🔐 Environment / Streamlit Secrets based configuration

---

## 🧠 Translation Pipeline

```text
                         LINGUAFLOW
                             │
                             ▼
                       SQLite Cache
                       │          │
                     HIT         MISS
                       │          │
                       ▼          ▼
                    Result   Gemini 2.5 Flash
                                  │
                           failure / quota
                                  ▼
                         Gemini Flash-Lite
                                  │
                           failure / quota
                                  ▼
                      NVIDIA Nemotron 3 Ultra
                                  │
                               failure
                                  ▼
                         TranslationError
```

A cache hit avoids an unnecessary AI request. On a cache miss, providers are attempted in order until a valid translation is returned or all available providers fail.

---

## 🏗️ Deployment Architecture

LinguaFlow supports two execution modes while keeping the same provider strategy.

### Local Development

```text
Streamlit
    ↓
Translator
    ↓
gemini_server.mjs
    ↓
Node.js :8765
    ↓
Google Gemini
```

Local mode:

```env
GEMINI_USE_LOCAL_SERVER=true
```

### Streamlit Cloud

The hosted application does **not** require Node.js or `gemini_server.mjs`.

```text
Streamlit Cloud
      ↓
Python Translator
      ↓
Google GenAI SDK
      ↓
Google Gemini
```

Cloud mode:

```toml
GEMINI_USE_LOCAL_SERVER = false
```

This hybrid design keeps local development convenient while allowing the deployed application to run without a separate Node.js backend.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Application | Python |
| Local AI service | Node.js |
| Google AI SDK | `google-genai` |
| Primary model | Gemini 2.5 Flash |
| Secondary model | Gemini Flash-Lite |
| Final fallback | NVIDIA Nemotron 3 Ultra |
| Cache | SQLite |
| Language detection | `langdetect` |
| HTTP communication | Requests |
| Configuration | `.env` / Streamlit Secrets |
| Deployment | Streamlit Cloud |

---

## 📁 Project Structure

```text
CodeAlpha_LinguaFlow/
│
├── app.py
├── gemini_server.mjs
├── load_test.py
├── package.json
├── package-lock.json
├── requirements.txt
├── README.md
├── .gitignore
│
└── src/
    ├── languages.py
    ├── language_detector.py
    ├── main.py
    └── translator.py
```

> `.env`, API credentials, and private runtime data should not be committed.

---

## ⚙️ Local Installation

### 1. Clone

```bash
git clone https://github.com/nabinchettri18/CodeAlpha_LinguaFlow.git
cd CodeAlpha_LinguaFlow
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 4. Install Node dependencies

```powershell
npm install
```

Node.js is required only for local Gemini-service mode.

### 5. Configure `.env`

Example:

```env
GEMINI_USE_LOCAL_SERVER=true

GOOGLE_API_KEY=your_google_api_key
GEMINI_API_KEY=your_google_api_key

GEMINI_URL=http://127.0.0.1:8765/translate
GEMINI_HEALTH_URL=http://127.0.0.1:8765/health

GEMINI_PRIMARY_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODEL=gemini-3.1-flash-lite

NVIDIA_API_KEY=your_nvidia_api_key
NVIDIA_CHAT_URL=https://integrate.api.nvidia.com/v1/chat/completions
NEMOTRON_MODEL=nvidia/nemotron-3-ultra-550b-a55b
```

### 6. Run

```powershell
python -m streamlit run app.py
```

---

## ☁️ Streamlit Cloud

Configure these values under **Manage app → Settings → Secrets**:

```toml
GOOGLE_API_KEY = "your_google_api_key"
GEMINI_USE_LOCAL_SERVER = false
NVIDIA_API_KEY = "your_nvidia_api_key"
```

The Cloud deployment then uses:

```text
Streamlit Cloud
      ↓
Python Translator
      ↓
Google GenAI SDK
      ↓
Gemini
```

No local port `8765` or Node.js process is required.

---

## 🔄 Provider Strategy

| Priority | Provider | Role |
|---|---|---|
| 1 | Gemini 2.5 Flash | Primary translation |
| 2 | Gemini Flash-Lite | Secondary fallback |
| 3 | NVIDIA Nemotron 3 Ultra | Final reliability fallback |

### Normal request

```text
Request
   ↓
SQLite Cache
   ↓ MISS
Gemini 2.5 Flash
   ↓
Success → Cache → Return
```

### Primary failure

```text
Gemini 2.5 Flash
       ↓ FAILURE
Gemini Flash-Lite
       ↓ SUCCESS
Cache → Return
```

### Complete Gemini failure

```text
Gemini 2.5 Flash
       ↓ FAIL
Gemini Flash-Lite
       ↓ FAIL
NVIDIA Nemotron 3 Ultra
       ↓ SUCCESS
Return Translation
```

---

## 🗄️ SQLite Cache

LinguaFlow checks the SQLite cache before making an AI request.

```text
Translation Request
       ↓
Cache Lookup
   ↙         ↘
 HIT         MISS
  ↓            ↓
Result       AI Provider
               ↓
           Translation
               ↓
           Save Cache
```

Caching reduces repeated API calls and improves response time for repeated translations.

---

## 🔍 Automatic Language Detection

Users can select **Auto-detect** as the source language. LinguaFlow uses its language detection module to determine the source language before translation.

---

## 🛡️ Reliability

Provider responses are validated before being accepted as successful translations.

```text
Provider Request
      ↓
Response Received
      ↓
Validate Output
   ↙          ↘
VALID        INVALID
 ↓             ↓
Return       Next Provider
```

The application also uses retry/cooldown behavior for transient failures and moves to the next provider when a provider becomes unavailable or rate-limited.

---

## 🧪 Nemotron Load Test

Nemotron was independently tested with **25 unique concurrent translation requests** while Gemini providers were intentionally skipped.

| Metric | Result |
|---|---:|
| Total requests | 25 |
| Successful | 25 |
| Failed | 0 |
| Success rate | 100% |
| Average latency | 160.69 s |
| Fastest | 128.40 s |
| Slowest | 489.55 s |
| P50 latency | 131.02 s |
| P95 latency | 419.86 s |
| P99 latency | 489.47 s |
| Throughput | 0.05 req/s |
| Overall status | **PASS** |

Nemotron's measured latency is substantially higher than the normal Gemini path, supporting its role as the final fallback rather than the primary provider.

---

## 🎓 CodeAlpha Internship Project

LinguaFlow is the completed project maintained for the **CodeAlpha internship/project workflow**.

### Project highlights

- Built a multilingual AI translation application
- Designed a resilient multi-provider architecture
- Integrated Google Gemini models
- Integrated NVIDIA Nemotron as a final fallback
- Implemented SQLite caching
- Added automatic language detection
- Implemented retry, cooldown, and output validation
- Created a local Node.js Gemini service
- Added a separate Streamlit Cloud execution path using the Google GenAI Python SDK
- Deployed the application on Streamlit Cloud
- Maintained the project with Git and GitHub

### Submission links

- **GitHub:** https://github.com/nabinchettri18/CodeAlpha_LinguaFlow
- **Live Demo:** https://linguaflowtranslate.streamlit.app/

---

## 💼 Portfolio 

### Description

> **LinguaFlow is an AI-powered multilingual translation platform built with Python and Streamlit. It uses SQLite caching and a resilient multi-provider architecture with Gemini 2.5 Flash as the primary translator, Gemini Flash-Lite as a secondary fallback, and NVIDIA Nemotron 3 Ultra as the final reliability provider. The application supports automatic language detection and separate local and Streamlit Cloud execution paths.**


- Built and deployed **LinguaFlow**, a multilingual AI translation platform using **Python, Streamlit, Google Gemini, NVIDIA Nemotron, SQLite, and language detection**.
- Designed a **multi-provider fallback architecture** that automatically switches from Gemini 2.5 Flash to Gemini Flash-Lite and Nemotron when providers fail or become unavailable.
- Implemented **SQLite caching, retry handling, output validation, and provider cooldown logic** to improve reliability and reduce repeated API requests.
- Deployed the application to **Streamlit Cloud** using the Google GenAI Python SDK while retaining a Node.js Gemini service for local development.

### Portfolio links

- **Live Demo:** https://linguaflowtranslate.streamlit.app/
- **GitHub:** https://github.com/nabinchettri18/CodeAlpha_LinguaFlow

---

## 📌 Current Limitations

- Nemotron is significantly slower than the normal Gemini path.
- Translation quality can vary by language and provider.
- External API availability, quotas, and rate limits can affect provider availability.
- The project is currently an internship/portfolio-scale application rather than a large public production service.
- User authentication and account management are not currently included.
- Advanced analytics and distributed infrastructure are not currently implemented.

---

## 🔮 Future Development

- Provider performance dashboard
- Detailed cache analytics
- Translation history
- User accounts and authentication
- Batch translation
- PDF/DOCX translation
- Voice translation
- Public API
- Mobile application
- Browser extension
- Distributed caching
- Horizontal scaling
- Automated multilingual quality evaluation

---

## 🔒 Security

Never publish:

- API keys
- `.env` files containing secrets
- Private credentials
- Service tokens

Use placeholders in documentation:

```env
GOOGLE_API_KEY=your_google_api_key
NVIDIA_API_KEY=your_nvidia_api_key
```

For Streamlit Cloud, store credentials in **Secrets**, not in the repository.

---

## 📊 Project Status

```text
Multilingual Translation            ✅
SQLite Cache                        ✅
Automatic Language Detection       ✅
Gemini Primary                      ✅
Gemini Flash-Lite Fallback          ✅
Nemotron Final Fallback             ✅
Provider Failure Handling           ✅
Local Development Mode              ✅
Streamlit Cloud Deployment          ✅
GitHub Repository                   ✅
Live Demo                           ✅
CodeAlpha Project                   ✅

Overall Status: STABLE / DEPLOYED
```

---

## LinguaFlow

**AI-powered multilingual translation with resilient provider fallback.**

**Created by Nabin Chettri.**
