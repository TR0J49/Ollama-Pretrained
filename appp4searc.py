from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import re
from googletrans import Translator, LANGUAGES  # Added for translation support
import json
from difflib import SequenceMatcher

app = Flask(__name__)

# Initialize components
print("🔄 Loading semantic model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
df = None
index = None
embeddings = None
translator = Translator()  # Initialize translator

# Supported languages with their codes
SUPPORTED_LANGUAGES = {
    'english': 'en',
    'hindi': 'hi',
    'marathi': 'mr',
    # Add more languages as needed
}

# Load data and build index
def initialize_system():
    global df, index, embeddings
    print("📂 Loading data...")
    df = pd.read_csv("API Dataset 129.csv")
    df.fillna("", inplace=True)
    print("🔨 Building FAISS index...")
    index, embeddings = build_faiss_index(df)

# 🔍 Preprocess user query
def preprocess_query(query):
    query = query.lower()
    query = re.sub(r"[^a-zA-Z0-9\s]", "", query)
    return query.strip()

# 🔍 Build FAISS index
def build_faiss_index(df):
    corpus = (df['Intent'].fillna('') + " " + df['API Name'].fillna('') + " " +
              df['Request Packet(s)'].fillna('') + " " + df['Response Packets']).tolist()
    embeddings = model.encode(corpus, convert_to_tensor=False)
    dimension = embeddings[0].shape[0]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))
    return index, embeddings

# 🌍 Detect and translate query to English
def process_user_query(query):
    try:
        detected = translator.detect(query)
        source_lang = detected.lang

        if source_lang == 'en':
            return query, 'english'

        translated = translator.translate(query, src=source_lang, dest='en').text
        return translated, next((lang for lang, code in SUPPORTED_LANGUAGES.items() if code == source_lang), 'english')
    except Exception as e:
        print(f"Translation error: {e}")
        return query, 'english'

# 🌍 Translate response to user's language
def translate_response(response, target_lang):
    if target_lang == 'english':
        return response

    try:
        lang_code = SUPPORTED_LANGUAGES.get(target_lang.lower(), 'en')
        translated = translator.translate(response, src='en', dest=lang_code).text
        return translated
    except Exception as e:
        print(f"Response translation error: {e}")
        return response + "\n\n(Note: Could not translate response to your language)"

# ✅ Extract attributes from Request Packet
def extract_attributes(request_packet_text):
    try:
        data = json.loads(request_packet_text)
        return list(data.keys())
    except:
        return re.findall(r'"(\w+)"\s*:', request_packet_text)

# ✅ Fuzzy match function
def fuzzy_match(a, b, threshold=0.7):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold

# ✅ Calculate attribute match across all fields
def calculate_attribute_match(query_tokens, attributes):
    match_count = 0
    for token in query_tokens:
        for attr in attributes:
            if token.lower() == attr.lower():
                match_count += 2  # Exact match weighted higher
            elif fuzzy_match(token, attr):
                match_count += 1  # Fuzzy match weighted lower
    return match_count

# ✅ Retrieve relevant context with multi-attribute matching and weighted ranking
def retrieve_relevant_context(user_query, max_results=10, threshold=1.2):
    query_tokens = user_query.split()

    query_embedding = model.encode([user_query])[0].astype('float32').reshape(1, -1)
    distances, indices = index.search(query_embedding, len(df))

    valid_results = []

    for i, d in zip(indices[0], distances[0]):
        if d <= threshold:
            row = df.iloc[i]

            # ✅ Collect attributes from multiple sources
            request_attrs = extract_attributes(row.get('Request Packet(s)', ''))
            extra_attrs = [
                row.get('API Name', ''),
                row.get('API Endpoint', ''),
                row.get('Intent', '')
            ]
            all_attributes = request_attrs + extra_attrs

            # ✅ Calculate attribute match count
            match_count = calculate_attribute_match(query_tokens, all_attributes)

            # ✅ Weighted score: attributes > semantic similarity
            weighted_score = (match_count * 2) + (1 / (d + 0.0001))

            valid_results.append((i, d, match_count, weighted_score))

    # ✅ Sort results by weighted score
    valid_results.sort(key=lambda x: x[3], reverse=True)
    valid_results = valid_results[:max_results]

    if not valid_results:
        return None

    # ✅ Build context for Gemini
    context = ""
    for idx, dist, match_count, score in valid_results:
        row = df.iloc[idx]
        context += f"""
API Name: {row.get('API Name', '')}
Intent: {row.get('Intent', '')}
API Endpoint: {row.get('API Endpoint', '')}
API URL(s): {row.get('API URL(s)', '')}
Request Packet(s): {row.get('Request Packet(s)', '')}
Response Packets: {row.get('Response Packets', '')}
Attribute Matches: {match_count}
Weighted Score: {round(score, 4)}
(Relevance Score: {round(1 - dist, 4)})
\n"""

    return context.strip()

# ✅ Generate response using Gemini API
def generate_journey_with_gemini(user_query, context, user_language='english'):
    api_key = "AIzaSyAjeFulYtt6sCt25p-hUklAYVw9MbKGk5Q"
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }

    if context:
        prompt = f"""
You are an API expert. The following APIs are ranked based on two criteria:
1. Number of attributes from the user's query that match the API's Request Packet, API Name, Endpoint, and Intent (most important).
2. Semantic similarity score (secondary factor).

APIs with higher attribute matches should be explained first. For each API:
- Explain why it was ranked high (e.g., matched attributes: userId, amount).
- Provide a structured answer with:
    1. API Name
    2. Purpose
    3. URL 
    4. Required Request Attributes (and their purpose)
    5. Request Body with fields
    6. Response Body structure
    7. Response Body with fields 
    8. How the matched attributes relate to the user query
    9. Implementation Steps

Context (sorted by ranking):
{context}
 
User Query:
{user_query}

Now write the best possible answer, prioritizing APIs with more attribute matches.
"""
    else:
        prompt = f"""
User asked (originally in {user_language}): "{user_query}"

No relevant API documentation found. Respond politely that you do not have sufficient information, and suggest alternative approaches or similar queries.
"""

    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(endpoint, headers=headers, json=data)

    if response.status_code == 200:
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            return "⚠️ Unexpected Gemini response format."
    else:
        return f"❌ Gemini API Error {response.status_code}: {response.text}"

#================================================================================================================================================
# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_query = request.form['query']
    print("user_query", user_query)
    if not user_query:
        return jsonify({'error': 'Please enter a query'})

    processed_query, user_language = process_user_query(user_query)
    print("processed_query,user_language", processed_query, user_language)
    processed_query = preprocess_query(processed_query)
    print("processed_query", processed_query)

    context = retrieve_relevant_context(processed_query)
    response = generate_journey_with_gemini(processed_query, context, user_language)
    print("response", response)

    if user_language != 'english':
        response = translate_response(response, user_language)

    return jsonify({
        'query': user_query,
        'response': response,
        'detected_language': user_language
    })

# Initialize system before first request
initialize_system()

if __name__ == '__main__':
    app.run(debug=True, port=9000, host='0.0.0.0')
