from openai import OpenAI
import os

# Manually load .env (simple key-value reader)
def load_env(file_path='.env'):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found")
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Load your .env
load_env()

# Now create client using loaded env vars
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE"),
)

# Test call to best Grok model
try:
    response = client.chat.completions.create(
        model="grok-4.20-reasoning",  # Best reasoning model
        messages=[
            {"role": "system", "content": "You are a helpful AI CEO."},
            {"role": "user", "content": "Say hello and tell me the current date and time in UTC."}
        ],
        temperature=0.7,
        max_tokens=100,
    )
    print("Grok response:")
    print(response.choices[0].message.content)
except Exception as e:
    print("Error:", str(e))