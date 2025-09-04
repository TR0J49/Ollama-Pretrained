from flask import Flask, render_template, request, jsonify, session
import requests
import json
import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Store conversation history per session
def get_conversation_history():
    if 'conversation' not in session:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session['conversation'] = [
            {
                "role": "system",
                "content": """You are ACE AI, an ICICI Bank FAQ Assistant.  
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
            "num_predict": 250,
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
    
    # Add user message to history
    conversation.append({"role": "user", "content": user_message})
    
    # Prepare the request to Ollama
    url = "http://localhost:11434/api/chat"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "model": settings["model"],
        "messages": conversation,
        "stream": False,
        "options": {
            "num_predict": settings["num_predict"],
            "temperature": settings["temperature"]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        if "message" in data and "content" in data["message"]:
            ai_response = data["message"]["content"]

            # ✅ Print in terminal for debugging
            print(f"\n[User]: {user_message}")
            print(f"[AI]: {ai_response}\n")

            # Add AI response to conversation history
            conversation.append({"role": "assistant", "content": ai_response})
            session['conversation'] = conversation
            
            return jsonify({'response': ai_response})
        else:
            return jsonify({'error': 'Invalid response from AI'}), 500
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")  # Print error in console
        return jsonify({'error': f'Error connecting to Ollama: {str(e)}'}), 500
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")  # Print error in console
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/new_chat', methods=['POST'])
def new_chat():
    session.pop('conversation', None)
    get_conversation_history()  # Reset to initial state
    return jsonify({'status': 'success'})

@app.route('/settings', methods=['POST'])
def update_settings():
    settings = get_settings()
    data = request.json
    
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
