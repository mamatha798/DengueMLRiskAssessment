
import time
import os
import re
import json
import urllib.request
import urllib.error
from pathlib import Path

from pypdf import PdfReader
from dotenv import load_dotenv

# Load Gemini API key
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

PDF_PATH = BASE_DIR / "medical_knowledge" / "who_dengue.pdf"

knowledge_chunks = []


# Kannada keywords mapped to English words found in the WHO PDF
KANNADA_KEYWORDS = {
    "ಡೆಂಗ್ಯೂ": ["dengue"],
    "ಹೇಗೆ": ["how"],
    "ಹರಡುತ್ತದೆ": ["spread", "transmission", "mosquito"],
    "ಹರಡುವುದು": ["spread", "transmission", "mosquito"],
    "ಸೊಳ್ಳೆ": ["mosquito"],
    "ಕಚ್ಚುವಿಕೆ": ["bite", "mosquito"],
    "ಜ್ವರ": ["fever"],
    "ಲಕ್ಷಣಗಳು": ["symptoms", "signs"],
    "ತಲೆನೋವು": ["headache"],
    "ವಾಂತಿ": ["vomiting"],
    "ರಕ್ತಸ್ರಾವ": ["bleeding"],
    "ಪ್ಲೇಟ್ಲೆಟ್": ["platelets", "platelet"],
    "ಅಪಾಯ": ["warning", "severe", "danger"],
    "ತಡೆಗಟ್ಟುವುದು": ["prevention", "prevent"],
    "ಚಿಕಿತ್ಸೆ": ["treatment", "care"],
}


def load_knowledge():
    """Extract WHO PDF text and divide it into overlapping chunks."""

    global knowledge_chunks

    if not PDF_PATH.exists():
        print("WHO PDF not found:", PDF_PATH)
        return

    try:
        reader = PdfReader(str(PDF_PATH))
        full_text = ""

        for page in reader.pages:
            full_text += (page.extract_text() or "") + "\n"

        full_text = re.sub(r"\s+", " ", full_text).strip()

        chunk_size = 180
        overlap = 40
        words = full_text.split()

        knowledge_chunks = []

        for start in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[start:start + chunk_size])

            if chunk:
                knowledge_chunks.append(chunk)

        print("WHO knowledge loaded successfully!")
        print("Total pages:", len(reader.pages))
        print("Knowledge chunks:", len(knowledge_chunks))

    except Exception as error:
        print("WHO PDF loading error:", error)


def retrieve_information(question, top_k=3):
    """Retrieve relevant WHO information using English and Kannada keywords."""

    if not knowledge_chunks:
        load_knowledge()

    question_lower = question.lower()

    question_words = set(
        re.findall(r"\b[a-zA-Z]{3,}\b", question_lower)
    )

    # Add English equivalents for Kannada words
    for kannada_word, english_words in KANNADA_KEYWORDS.items():
        if kannada_word in question:
            question_words.update(english_words)

    # Support common Kannada-English transliteration
    transliteration_keywords = {
        "dengue": ["dengue"],
        "hege": ["how"],
        "haradutte": ["spread", "transmission", "mosquito"],
        "haradutthe": ["spread", "transmission", "mosquito"],
        "solle": ["mosquito"],
        "jwara": ["fever"],
        "lakshanagalu": ["symptoms", "signs"],
        "thale novu": ["headache"],
        "vomiting": ["vomiting"],
        "platelet": ["platelets", "platelet"],
    }

    for phrase, english_words in transliteration_keywords.items():
        if phrase in question_lower:
            question_words.update(english_words)

    scored_chunks = []

    for chunk in knowledge_chunks:
        chunk_words = set(
            re.findall(r"\b[a-zA-Z]{3,}\b", chunk.lower())
        )

        score = len(question_words.intersection(chunk_words))

        if score > 0:
            scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)

    return [chunk for score, chunk in scored_chunks[:top_k]]


def ask_dengue(question):
    """Retrieve WHO information and generate a grounded Gemini answer."""

    results = retrieve_information(question)

    if not results:
        return (
            "I could not find relevant information in the WHO knowledge "
            "document. Please consult a qualified healthcare professional."
        )

    context = "\n\n".join(results)

    prompt = f"""
You are Dengue AI Guardian, a health education assistant.

Answer using ONLY the WHO information provided below.

IMPORTANT SAFETY RULES:
- Do not diagnose dengue.
- Do not invent medical facts or statistics.
- If the WHO information is insufficient, clearly say so.
- Explain warning signs in simple language.
- Recommend urgent medical evaluation for severe warning signs.
- Do not prescribe medicines or replace a healthcare professional.
- Never claim that platelet count alone determines dengue severity.
- Keep the answer clear and understandable.

LANGUAGE RULES:
- If the user asks in Kannada, answer in Kannada.
- If the user asks in English, answer in English.
- If the user asks in Kannada-English mix, answer in simple Kannada-English.
- Keep medical terms understandable.

WHO SOURCE:
{context}

USER QUESTION:
{question}

Give a simple and helpful answer.
"""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return (
            "Gemini API key is missing.\n\n"
            "Retrieved WHO information:\n" + context
        )

    api_url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-3.8-flash:generateContent"
    )

    request_data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 512,
            "thinkingConfig": {
                "thinkingBudget": 0
            }
        }
    }

    url = api_url + "?key=" + api_key

    for attempt in range(3):
        try:
            print(f"Connecting to Gemini (attempt {attempt + 1}/3)...")

            request = urllib.request.Request(
                url,
                data=json.dumps(request_data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))

            candidates = result.get("candidates", [])

            if not candidates:
                raise ValueError("Gemini returned no answer.")

            parts = candidates[0].get("content", {}).get("parts", [])

            answer = "\n".join(
                part.get("text", "")
                for part in parts
                if part.get("text")
            ).strip()

            if not answer:
                raise ValueError("Gemini returned empty text.")

            return (
                answer
                + "\n\nSource: WHO Dengue and severe dengue fact sheet."
            )

        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
            ValueError
        ) as error:

            print(f"Gemini attempt {attempt + 1} failed: {error}")

            if attempt < 2:
                wait_seconds = 2 ** (attempt + 1)
                print(f"Retrying in {wait_seconds} seconds...")
                time.sleep(wait_seconds)

            else:
                print("All Gemini attempts failed.")

    return (
        "Gemini is temporarily unavailable after 3 attempts.\n\n"
        "Retrieved WHO information:\n"
        + context
        + "\n\nSource: WHO Dengue and severe dengue fact sheet."
    )


if __name__ == "__main__":
    load_knowledge()

    print("\nDengue AI Guardian - RAG Test")

    while True:
        question = input(
            "\nAsk a dengue question (type exit to stop): "
        )

        if question.strip().lower() in ["exit", "quit"]:
            print("Thank you for using Dengue AI Guardian!")
            break

        if not question.strip():
            print("Please enter a question.")
            continue

        print("\nGenerating answer...\n")
        print(ask_dengue(question))
