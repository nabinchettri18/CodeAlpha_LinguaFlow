# 🌐 LinguaFlow

## Language Translation Tool

LinguaFlow is a user-friendly language translation web application developed using Python and Streamlit.

The application allows users to enter text, automatically detect the source language, select a target language, and translate the text using a locally hosted LibreTranslate REST API.

LinguaFlow also provides useful productivity and accessibility features such as translation history, copy-to-clipboard, text-to-speech, clear controls, input validation, and language-detection safeguards.

---

## 📌 Project Information

| Field | Details |
|---|---|
| Project Name | LinguaFlow |
| Project Type | Language Translation Tool |
| Internship | CodeAlpha Internship |
| Task | Task 1 — Language Translation Tool |
| Frontend | Streamlit |
| Backend | Python |
| Translation Service | LibreTranslate REST API |
| Language Detection | LangDetect + custom heuristics |
| Repository | CodeAlpha_LinguaFlow |

---

## 🎯 Project Objective

The objective of LinguaFlow is to create a simple translation workspace where users can quickly translate text between supported languages without dealing with a complicated interface.

The application focuses on four main areas:

1. **Simple user experience**
2. **Automatic language detection**
3. **Reliable API-based translation**
4. **Useful translation utilities**

The project was developed as part of the CodeAlpha Internship Task 1 — Language Translation Tool.

---

## ✨ Features

### 🌍 Automatic Language Detection

LinguaFlow automatically attempts to identify the language of the entered text.

The detection system combines:

- `langdetect`
- Unicode/script detection
- Common English word detection
- Short-text handling
- Confidence checking
- Informal English input handling

Example:

```text
Hello how are you
        ↓
English
```

Hindi example:

```text
नमस्ते आप कैसे हैं
        ↓
Hindi
```

Short informal inputs are handled more carefully:

```text
Hlo
 ↓
English
```

instead of allowing statistical detection to incorrectly classify the text as an unrelated language.

---

## 🔄 Text Translation

LinguaFlow communicates with a locally hosted LibreTranslate REST API.

The translation workflow is:

```text
User Input
    ↓
Language Detection
    ↓
Source Language
    ↓
Target Language Selection
    ↓
LibreTranslate REST API
    ↓
Translated Text
```

---

## 📋 Copy Translation

Users can copy the translated text directly using the **Copy** button.

---

## 🔊 Listen to Translation

LinguaFlow provides a **Listen** feature that allows users to hear the translated text using text-to-speech functionality.

---

## 🗑️ Clear Translation

The **Clear** control allows users to quickly remove the current translation workspace content and start a new translation.

---

## 🕘 Translation History

LinguaFlow provides a translation history feature so users can refer back to previous translations during the current application session.

---

## ⚠️ Error Handling

LinguaFlow handles:

- Empty input
- Missing source language
- Missing target language
- Failed language detection
- Low-confidence detection
- Translation service connection failures
- Invalid API responses
- Empty translation responses

The application attempts to present readable error messages instead of raw backend exceptions.

---

## 🧠 Language Detection Architecture

The language detector combines script detection, English heuristics, short-input handling, statistical detection, and confidence checks.

```text
User Text
    ↓
Empty Input Check
    ↓
Script Detection
    ↓
English Heuristics
    ↓
LangDetect
    ↓
Confidence Check
    ↓
Final Language
```

This additional logic helps reduce incorrect classifications for short inputs.

---

## 🌐 Translation API Architecture

```text
Streamlit Application
        │
        │ HTTP POST
        ▼
Translator Class
        │
        ▼
LibreTranslate
        │
        ▼
Translation Response
        │
        ▼
Streamlit UI
```

The translation client validates input before making the API request and handles connection failures and invalid responses.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Web interface |
| LibreTranslate | Translation REST API |
| Requests | HTTP API communication |
| LangDetect | Statistical language detection |
| HTML/CSS/JavaScript | UI enhancements where applicable |

---

## 📂 Project Structure

```text
LinguaFlow/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── src/
│   ├── language_detector.py
│   └── translator.py
│
└── tests/
```

### `app.py`

Contains the main Streamlit application and user interface.

### `src/language_detector.py`

Contains language detection logic including script detection, English heuristics, short-input handling, and confidence protection.

### `src/translator.py`

Contains the translation client used to communicate with the LibreTranslate REST API.

### `requirements.txt`

Contains the Python dependencies required by the application.

### `.gitignore`

Prevents unnecessary files such as virtual environments and Python cache files from being committed.

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/nabinchettri18/CodeAlpha_LinguaFlow.git
cd CodeAlpha_LinguaFlow
```

### 2. Create a Virtual Environment

On Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## 🌐 Running LibreTranslate

LinguaFlow currently uses a locally hosted LibreTranslate service during development.

Start LibreTranslate:

```powershell
libretranslate
```

The service should become available at:

```text
http://127.0.0.1:5000
```

Verify the service:

```powershell
Test-NetConnection 127.0.0.1 -Port 5000
```

A successful service should report:

```text
TcpTestSucceeded : True
```

You can also check available languages:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/languages" -Method Get
```

---

## 🚀 Running LinguaFlow

Keep LibreTranslate running in one terminal.

Open another terminal and activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then start Streamlit:

```powershell
streamlit run app.py
```

---

## 🧪 Example

### English → Hindi

**Input:**

```text
My name is Nabin
```

**Detected Language:**

```text
English
```

**Target Language:**

```text
Hindi
```

**Example Translation:**

```text
मेरा नाम नैबिन है
```

---

## 🔬 Example Language Detection

| Input | Detected Language |
|---|---|
| `Hlo` | English |
| `Hello how are you` | English |
| `नमस्ते आप कैसे हैं` | Hindi |
| `হ্যালো, তুমি কেমন আছো` | Bengali |

Short-input handling was added because statistical language detection can be unreliable when only a few characters are provided.

---

## 🛡️ Input Validation

Examples:

```text
Empty input
    ↓
Validation error
```

```text
Missing target language
    ↓
Validation error
```

```text
Translation service unavailable
    ↓
User-friendly error
```

---

## 📡 API Communication

The translation request follows the general REST structure:

```text
POST /translate
```

with:

```text
q       → Text to translate
source  → Source language
target  → Target language
format  → text
```

The service returns translated text, which LinguaFlow displays in the UI.

---

## 🖥️ Application Workflow

```text
1. User opens LinguaFlow
          ↓
2. User enters text
          ↓
3. LinguaFlow detects the source language
          ↓
4. User selects target language
          ↓
5. Translation request is sent
          ↓
6. LibreTranslate processes the request
          ↓
7. Translation is returned
          ↓
8. Translation is displayed
          ↓
9. User can Copy / Listen / Clear
          ↓
10. Translation can be retained in History
```

---

## 📸 Screenshots

Add project screenshots here for the CodeAlpha submission.

Recommended screenshots:

- Main translation interface
- Translation result
- Translation history
- Error handling

---

## ⚠️ Current Limitations

The current version uses a **locally hosted LibreTranslate instance**.

Therefore, the translation service must be running for LinguaFlow to perform translations.

The current development endpoint is:

```text
http://127.0.0.1:5000
```

For public deployment, the translation service should be hosted separately or replaced with a publicly accessible translation API.

---

## 🚀 Future Enhancements

Potential improvements include:

- Cloud-hosted translation service
- Public production deployment
- Persistent translation history
- User authentication
- Database-backed history
- Voice input
- Improved text-to-speech controls
- Document translation
- File upload and translation
- Translation export
- Additional language support
- Translation caching
- API request optimization
- Advanced language detection
- Mobile-focused UI improvements

---

## 🎓 CodeAlpha Internship

LinguaFlow was developed as part of the:

**CodeAlpha Internship**

### Language Translation Tool

The project demonstrates:

- API-based translation
- Automatic language detection
- Interactive user interface
- Error handling
- Translation utilities
- Python application development

---

## 👨‍💻 Developer

### Nabin Chettri

**B.Tech — Artificial Intelligence & Machine Learning**

---

## 📜 License

This project was created for educational and internship purposes as part of the CodeAlpha Internship.

---

## ⭐ Project

**LinguaFlow — Language Translation Tool**

Built with Python, Streamlit, LangDetect, Requests, and LibreTranslate.
