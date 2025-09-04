import requests
import json

# Store conversation history
# Store conversation history with knowledge
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

3. Company: Prevoyance IT Solutions Pvt. Ltd. (aka Prevoyance Solutions)
   - Founder: Prafulla Nathile
   - Headquarters: Nagpur, Maharashtra, India
   - Founded: 2009 | Incorporated: 20 Jan 2022 | CIN: U72900MH2022PTC375237
   - Status: Active (Unlisted) | Team: 101–250 employees
   - Services:
     • Software & App Development (Mobile, Web, UI/UX, Custom Solutions)
     • Cloud & Infrastructure (Migration, Hybrid/Multi-Cloud, DR)
     • Digital Transformation (AI, IoT, Cloud Strategy)
     • Software Testing (All stages, Nagpur & Mumbai ops)
     • Product Engineering & Team Augmentation
     • Cybersecurity & Compliance
   - Industries: Banking, Healthcare, Education, Manufacturing, etc.
   - Offices:
     • Nagpur: 17/1 Amar Plaza, IT Park Rd, Nagpur – 440022 | +91-95794-37780, +91-99708-50512 | info@prevoyancesolutions.com
     • Mumbai (BKC): Level 11, Platina, C-59, G-Block, Bandra Kurla Complex, Mumbai – 400051 | +91-22-6884-1727
"""
    }
]


# ANSI colors for nicer output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Default settings
settings = {
    "model": "llama3:8b",   # or "llama3:latest"
    "num_predict": 250,
    "temperature": 0.7
}

def ace_ai_chat(prompt):
    """Chat with ACE AI using Ollama's API dynamically with memory + settings."""
    url = "http://localhost:11434/api/chat"
    headers = {"Content-Type": "application/json"}

    # Add user message to history
    conversation.append({"role": "user", "content": prompt})

    payload = {
        "model": settings["model"],
        "messages": conversation,
        "stream": True,
        "options": {
            "num_predict": settings["num_predict"],
            "temperature": settings["temperature"]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=120)
    except requests.exceptions.RequestException as e:
        print(f"\n⚠️ Error connecting to Ollama: {e}")
        return ""

    output = ""
    print(f"{GREEN}ACE AI:{RESET}", end=" ", flush=True)

    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            if "message" in data and "content" in data["message"]:
                chunk = data["message"]["content"]
                print(chunk, end="", flush=True)
                output += chunk
            if data.get("done", False):
                break

    print()  # newline after response

    # Save ACE AI response to history
    conversation.append({"role": "assistant", "content": output})
    return output.strip()


# 🔹 Interactive loop with dynamic commands
print(f"{BLUE}🤖 Welcome to ACE AI Chat (type 'exit' to quit, 'new chat' to reset){RESET}\n")

while True:
    user_input = input(f"{BLUE}You:{RESET} ")

    if user_input.lower() in ["exit", "quit", "bye"]:
        print(f"{GREEN}👋 Goodbye! ACE AI signing off.{RESET}")
        break
    elif user_input.lower() == "new chat":
        conversation.clear()
        print(f"{YELLOW}✨ New conversation started!{RESET}")
        continue
    elif user_input.lower().startswith("set model "):
        settings["model"] = user_input.split("set model ", 1)[1]
        print(f"{YELLOW}⚙️ Model set to: {settings['model']}{RESET}")
        continue
    elif user_input.lower().startswith("set temp "):
        try:
            settings["temperature"] = float(user_input.split("set temp ", 1)[1])
            print(f"{YELLOW}⚙️ Temperature set to: {settings['temperature']}{RESET}")
        except ValueError:
            print(f"{YELLOW}⚠️ Invalid temperature value.{RESET}")
        continue
    elif user_input.lower().startswith("set tokens "):
        try:
            settings["num_predict"] = int(user_input.split("set tokens ", 1)[1])
            print(f"{YELLOW}⚙️ Max tokens set to: {settings['num_predict']}{RESET}")
        except ValueError:
            print(f"{YELLOW}⚠️ Invalid token number.{RESET}")
        continue

    ace_ai_chat(user_input)
