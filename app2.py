from flask import Flask, request, jsonify
import requests
import json

# -----------------------------
# Conversation Memory
# -----------------------------
conversation = [
    {
        "role": "system",
        "content": """You are ACE AI, a helpful and knowledgeable assistant.
        
Known Profiles:
1. User (Shubham Rahangdale)
   - From: Bhopal, Madhya Pradesh, India
   - Studies: B.Tech in Artificial Intelligence and Machine Learning (Final  year)
   - Interests: Startups, AI projects, Data Analytics
   - Founder: Neuro Tech Enclave Pvt Ltd

2. Nikky Bisen
   - Current Roles: PromptOps, AI Backer, CodeSynthist, Python | Flask Developer
   - Past: Prevoyance IT Solutions Pvt. Ltd.
   - Contact: Phone: 8007289776 | Email: nkbisane@gmail.com
   - Address: Nagpur, India
   - Online: LinkedIn: linkedin.com/in/nikky-bisen-4a609115a | Blog: clusterandcloud.blogspot.com

3. Company: Prevoyance IT Solutions Pvt. Ltd.
   - Founder: Prafulla Nathile
   - Headquarters: Nagpur, Maharashtra, India
   - Founded: 2009 | Incorporated: 20 Jan 2022 | CIN: U72900MH2022PTC375237
   - Status: Active (Unlisted) | Team: 101–250 employees
   - Services: Software, Cloud, Digital Transformation, Cybersecurity, etc.
"""
    }
]

# -----------------------------
# Settings
# -----------------------------
settings = {
    "model": "llama3:8b",
    "num_predict": 250,
    "temperature": 0.7
}

# -----------------------------
# ACE AI Function
# -----------------------------
def ace_ai_chat(prompt):
    """Chat with ACE AI using Ollama API (with memory)."""
    url = "http://localhost:11434/api/chat"
    headers = {"Content-Type": "application/json"}

    # Add user input to history
    conversation.append({"role": "user", "content": prompt})

    payload = {
        "model": settings["model"],
        "messages": conversation,
        "stream": False,   # Flask works better with full response
        "options": {
            "num_predict": settings["num_predict"],
            "temperature": settings["temperature"]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"⚠️ Error connecting to Ollama: {e}"

    # Extract content
    output = ""
    if "message" in data and "content" in data["message"]:
        output = data["message"]["content"]

    # Save to conversation history
    conversation.append({"role": "assistant", "content": output})
    return output.strip()

# -----------------------------
# Flask App
# -----------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 ACE AI Flask Server is running!"

@app.route("/chat", methods=["POST"])
def chat():
    user_data = request.json
    if not user_data or "prompt" not in user_data:
        return jsonify({"error": "No prompt provided"}), 400

    user_prompt = user_data["prompt"]
    reply = ace_ai_chat(user_prompt)

    return jsonify({
        "user": user_prompt,
        "assistant": reply
    })

@app.route("/reset", methods=["POST"])
def reset_chat():
    conversation.clear()
    return jsonify({"message": "✨ Conversation history cleared!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)