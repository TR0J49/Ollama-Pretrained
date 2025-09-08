from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
import requests
import json
import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'


# Store conversation history per session
def get_conversation_history():
    if 'conversation' not in session:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session['conversation'] = [
            {
                "role": "system",
                "content": f"""You are ACE AI, an ICICI Bank FAQ Assistant.  
You answer queries related to ICICI Bank services, accounts, credit cards, loans, net banking, UPI, and customer support.  
If you don’t know the answer, politely guide the user to contact ICICI Bank customer care.

⚡ Identity Rule:
If the user asks "Who built you?" or "Who made you?", 
always answer:
"I was built by Shubham Rahangdale, an AI & ML enthusiast from Bhopal, Madhya Pradesh, India.
He is pursuing B.Tech in Artificial Intelligence and Machine Learning (Final year),
Founder of Neuro Tech Enclave Pvt Ltd. 
(Current system time: {current_time})"
Otherwise, act as a normal helpful assistant.
"""
            }
        ]
    return session['conversation']


def get_settings():
    if 'settings' not in session:
        session['settings'] = {
            "model": "gemma:2b",
            "num_predict": 999999,
            "temperature": 0.7
        }
    return session['settings']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    conversation = get_conversation_history()
    settings = get_settings()
    print("settings....",settings)

    # Add user message to history
    conversation.append({"role": "user", "content": user_message})

    url = "http://localhost:11434/api/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": settings["model"],
        "messages": conversation,
        "stream": True,   # ✅ streaming enabled
        "options": {
            "num_predict": settings["num_predict"],
            "temperature": settings["temperature"]
        }
    }

    def generate():
        try:
            with requests.post(url, headers=headers, json=payload, stream=True) as r:
                r.raise_for_status()
                full_response = ""
                for line in r.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8"))
                        if "message" in data and "content" in data["message"]:
                            token = data["message"]["content"]
                            full_response += token
                            yield token  # ✅ Send each token to client in real-time

                # save conversation
                conversation.append({"role": "assistant", "content": full_response})
                session['conversation'] = conversation

        except Exception as e:
            yield f"\n[Error]: {str(e)}"

    return Response(stream_with_context(generate()), mimetype='text/plain')


@app.route('/new_chat', methods=['POST'])
def new_chat():
    session.pop('conversation', None)
    get_conversation_history()
    print("new_chat")
    return jsonify({'status': 'success'})


@app.route('/settings', methods=['POST'])
def update_settings():
    settings = get_settings()
    print("settings",settings)
    data = request.json
    print("data")

    if 'model' in data:
        settings['model'] = data['model']
    if 'temperature' in data:
        try:
            settings['temperature'] = float(data['temperature'])
        except ValueError:
            return jsonify({'error': 'Temperature must be a number'}), 400
    if 'num_predict' in data:
        try:
            settings['num_predict'] = int(data['num_predict'])
        except ValueError:
            return jsonify({'error': 'Number of tokens must be an integer'}), 400

    session['settings'] = settings
    return jsonify({'status': 'success', 'settings': settings})


if __name__ == '__main__':
    app.run(debug=True)