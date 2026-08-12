# 🌐 LinguaFlow

**AI-Powered Multilingual Translation Platform**

LinguaFlow is a resilient multilingual translation platform built around an intelligent provider-fallback architecture. It combines **SQLite caching** with multiple AI translation providers so temporary provider failures do not immediately result in a failed translation request.

---

## ✨ Overview

LinguaFlow uses a hierarchical translation pipeline:

```text
                    LINGUAFLOW
                        │
                        ▼
                  SQLite Cache
                   │         │
                  HIT       MISS
                   │         │
                   ▼         ▼
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

The cache is checked first. On a cache miss, LinguaFlow attempts the AI providers in order. If a provider fails or becomes unavailable, the system automatically moves to the next provider.

---

# 🚀 Key Features

- 🌍 Multilingual AI translation
- ⚡ SQLite translation caching
- 🤖 Gemini 2.5 Flash primary provider
- 🔄 Gemini Flash-Lite secondary fallback
- 🛡️ NVIDIA Nemotron 3 Ultra final fallback
- 🔍 Automatic language detection
- ✅ Translation output validation
- 🧩 Streamlit user interface
- 🔐 Environment-based API configuration
- 🧪 Independent provider testing
- ♻️ Graceful provider failure handling

---

# 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python |
| AI service layer | Node.js |
| Primary model | Gemini 2.5 Flash |
| Secondary model | Gemini Flash-Lite |
| Final fallback | NVIDIA Nemotron 3 Ultra |
| Cache | SQLite |
| API communication | HTTP / OpenAI-compatible API |
| Configuration | `.env` |
| Python package management | pip |
| Node package management | npm |

---

# 📁 Project Structure

```text
LinguaFlow/
│
├── app.py
├── gemini_server.mjs
├── linguaflow_cache.db
├── load_test.py
├── package.json
├── package-lock.json
├── requirements.txt
├── README.md
├── .env
├── .gitignore
│
└── src/
    ├── languages.py
    ├── language_detector.py
    ├── main.py
    └── translator.py
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/nabinchettri18/CodeAlpha_LinguaFlow
cd LinguaFlow
```

## 2. Create a Python virtual environment

```bash
python -m venv .venv
```

## 3. Activate the environment

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. Install Python dependencies

```powershell
pip install -r requirements.txt
```

## 5. Install Node.js dependencies

```powershell
npm install
```

## 6. Configure environment variables

Create or update the `.env` file. Use your project's actual variable names and keep real credentials private.

Example:

```env
GEMINI_URL=http://127.0.0.1:8765/translate
GEMINI_HEALTH_URL=http://127.0.0.1:8765/health

GEMINI_PRIMARY_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODEL=gemini-3.1-flash-lite

NVIDIA_CHAT_URL=https://integrate.api.nvidia.com/v1/chat/completions
NVIDIA_API_KEY=your_nvidia_api_key
NEMOTRON_MODEL=nvidia/nemotron-3-ultra-550b-a55b
```

> **Security:** Never commit real API keys or credentials to GitHub. Keep `.env` private.

## 7. Start LinguaFlow

```powershell
python -m streamlit run app.py
```

---

# 🏗️ Architecture & Provider Strategy

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

### Primary provider failure

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

| Priority | Provider | Role |
|---|---|---|
| 1 | Gemini 2.5 Flash | Primary translation |
| 2 | Gemini Flash-Lite | Secondary fallback |
| 3 | NVIDIA Nemotron 3 Ultra | Final fallback |

Nemotron is intentionally positioned as the **final reliability fallback**, rather than the normal high-speed translation path.

---

# 🗄️ SQLite Cache

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

A cache hit avoids an unnecessary AI API request, providing lower latency, fewer API calls, reduced provider usage, and faster repeated translations.

---

# 🔍 Language Detection

LinguaFlow includes automatic source-language detection. Users can select **Auto-detect**, allowing the system to determine the source language before translation.

---

# 🛡️ Reliability

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

If every provider fails, LinguaFlow returns a controlled translation error instead of silently returning an invalid result.

---

# 🧪 Nemotron 25-Request Test

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

### Interpretation

Nemotron successfully handled **25/25 requests** with **0 failures**. Its measured latency is substantially higher than the normal Gemini path, so Nemotron is kept as the **last-resort reliability provider**, not the primary translation engine.

---

# 📌 Current Limitations

- Nemotron is significantly slower than the normal Gemini path.
- Nemotron is intended as the final fallback rather than the normal translation provider.
- Translation quality can vary by language and provider.
- External API availability can affect translation availability.
- API quotas and rate limits can affect provider availability.
- The current application is primarily a project/prototype rather than a public production-scale service.
- A dedicated user authentication/account system is not currently included.
- A full cloud-scale deployment architecture has not yet been implemented.

---

# 🔮 Future Development

The current implementation is considered stable for the project scope. The following improvements are intentionally reserved for future development.

## Analytics

- Advanced translation analytics
- Provider performance dashboard
- Detailed cache analytics
- Request statistics
- Latency monitoring

## User Features

- User accounts
- Authentication
- Translation history
- Saved translations
- User preferences

## Translation Capabilities

- Batch translation
- PDF translation
- DOCX translation
- Voice translation
- Speech-to-text
- Text-to-speech
- More specialized translation models

## Platform Development

- Cloud deployment
- Public API
- Mobile application
- Browser extension
- Enterprise translation features

## Infrastructure

- Advanced monitoring
- Automatic provider health monitoring
- Distributed caching
- Latency optimization
- Horizontal scaling
- More extensive multilingual quality evaluation

These features are future development items and are not required for the current stable project implementation.

---

# 🔒 Security

Never publish:

- API keys
- `.env` files containing secrets
- Private credentials
- Service tokens

Use placeholders in documentation:

```env
NVIDIA_API_KEY=your_nvidia_api_key
```

Keep real credentials only in the local `.env` file.

---

# 🎯 Project Goal

LinguaFlow demonstrates how a multilingual AI application can combine:

- Artificial intelligence
- Provider redundancy
- Intelligent caching
- Automatic language detection
- Output validation
- Graceful failure handling

into a practical translation platform.

The main goal is not simply to translate text, but to demonstrate a **resilient AI architecture** capable of continuing to operate when an individual provider becomes unavailable.

---

# 💡 Project Positioning

> **LinguaFlow is a resilient AI-powered multilingual translation platform that combines intelligent SQLite caching with a hierarchical AI-provider architecture. Gemini 2.5 Flash handles primary translation, Gemini Flash-Lite provides secondary resilience, and NVIDIA Nemotron 3 Ultra acts as the final fallback when the primary services become unavailable.**

---

# 🚀 Status

```text
Production Translation Pipeline    ✅
SQLite Cache                       ✅
Language Detection                 ✅
Gemini Primary                     ✅
Gemini Flash-Lite Fallback         ✅
Nemotron Final Fallback            ✅
25-Request Nemotron Test           ✅
Project Documentation              ✅
```

**Overall Project Status: STABLE**

---

## LinguaFlow

**AI-powered multilingual translation with resilient provider fallback.**

**Created by : Nabin Chettri.**