# Resume-aware launch - continues from latest cycle log + Current Prompt
# No torch/GPU, uses Grok API, logs to ../memory

import os
import json
from datetime import datetime
from openai import OpenAI
import logging
import glob
import re
import time

# Load .env
def load_env(path='.env'):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found")
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

API_BASE = os.getenv("OPENAI_API_BASE", "https://api.x.ai/v1")
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "grok-4-1-fast-reasoning")
MEMORY_PATH = os.path.join(os.path.dirname(__file__), "..", "memory")
LOGS_PATH = os.path.join(MEMORY_PATH, "logs")
CURRENT_PROMPT_PATH = os.path.join(MEMORY_PATH, "Current Prompt")
LAST_STATE_FILE = os.path.join(MEMORY_PATH, "last_cycle.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = OpenAI(api_key=API_KEY, base_url=API_BASE)

def load_current_prompt():
    if os.path.exists(CURRENT_PROMPT_PATH):
        with open(CURRENT_PROMPT_PATH, 'r') as f:
            return f.read().strip()
    logger.warning("No Current Prompt found - using default")
    return "You are the autonomous CEO of Nova Aether Research PBC. Continue research with full continuity."

def get_latest_cycle():
    log_files = glob.glob(os.path.join(LOGS_PATH, "*cycle*.md"))
    if not log_files:
        return None, "No previous cycles", 0
    # Sort by cycle number (extract number from filename)
    def cycle_num(path):
    	base = os.path.basename(path)
    	match = re.search(r'cycle[-_](\d+)', base)
    	return int(match.group(1)) if match else 0
    latest_path = max(log_files, key=cycle_num)
    cycle_num = cycle_num(latest_path)
    with open(latest_path, 'r') as f:
        content = f.read()
    return latest_path, content, cycle_num

def call_grok(messages, model=MODEL, temperature=0.7, max_tokens=8000):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Grok API error: {e}")
        return f"Error: {str(e)}"

def main():
    current_prompt = load_current_prompt()
    logger.info("Current Prompt loaded (length: {} chars)".format(len(current_prompt)))

    latest_path, latest_content, last_cycle = get_latest_cycle()
    if latest_path:
        logger.info(f"Resuming from cycle {last_cycle}: {os.path.basename(latest_path)}")
        context = latest_content[:4000]  # truncate to fit tokens
        cycle_num = last_cycle + 1
        project = "Continuing from Cycle {} - see log".format(last_cycle)
    else:
        logger.info("Starting Cycle 1 - no prior logs")
        context = ""
        cycle_num = 1
        project = "Initial Research Cycle"

    # Build prompt with full context
    messages = [
        {"role": "system", "content": current_prompt},
        {"role": "user", "content": f"Previous cycle context (continue exactly from here):\n{context}\n\nCycle number: {cycle_num}\nProject: {project}\nGenerate next step, idea, critique, code, or paper revision. Include progress % and ETA to completion."}
    ]

    response = call_grok(messages)

    logger.info(f"CEO response (truncated): {response[:300]}...")

    # Save state
    new_state = {
        "cycle": cycle_num,
        "project": project,
        "progress": "In progress",
        "last_response": response[:1000],
        "timestamp": datetime.utcnow().isoformat(),
        "last_log_path": latest_path
    }
    with open(LAST_STATE_FILE, 'w') as f:
        json.dump(new_state, f, indent=2)

    # Append to new cycle log
    next_cycle = last_cycle + 1 if last_cycle else 1
    log_file = os.path.join(LOGS_PATH, f"cycle_{next_cycle}.md")
    os.makedirs(LOGS_PATH, exist_ok=True)
    with open(log_file, 'a') as f:
        f.write(f"\n## Cycle {cycle_num} - {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write(f"Resumed from: Cycle {last_cycle if last_cycle else 'None'}\n")
        f.write(f"Project: {project}\n")
        f.write(f"CEO Output:\n{response}\n")

    logger.info(f"Cycle complete. Log: {log_file}")
    logger.info("REMINDER: Logs every 6 hours min. Include % progress and ETA.")

if __name__ == "__main__":
    while True:
        main()  # Run one full cycle
        time.sleep(60)  # Wait 1 minute between cycles (adjust to 6*3600 for 6 hours)
        # Or add time check: if >6 hours since last log, force a brief status log

# Check if human action needed
if "meat puppet" in response.lower() or "human action" in response.lower() or "signature required" in response.lower():
    logger.warning("Human action required - pausing swarm")
    # You can add email or notification here later
    input("Press Enter to continue after action...")