import requests
import os
import json
import time
from datetime import datetime

env = os.environ.get

steam_id = env("steam_id")
base_url = env("leetify_url")
leetify_url = f"{base_url}{steam_id}"
llm_url = env("llm_url")
state_file = env("state_file")
webhook_url = env("webhook_url")


def is_new_match(current_match_id):
    if not os.path.exists(state_file):
        with open(state_file, "w") as f:
            json.dump({"last_id": current_match_id}, f)
        return True

    with open(state_file, "r") as f:
        state = json.load(f)

    if state["last_id"] != current_match_id:
        with open(state_file, "w") as f:
            json.dump({"last_id": current_match_id}, f)
        return True

    return False


def get_latest_match():
    if not steam_id:
        print("Error! No SteamID found in environment variables")
        return None

    response = requests.get(leetify_url)

    if response.status_code == 200:
        data = response.json()
        latest_match = data['recent_matches'][0]
        return latest_match
    else:
        print(f"Failed! Error code: {response.status_code}")
        return None


def send_data_to_ai(latest_match):
    print(f"Preparing data for match on {latest_match['map_name']}...")
    match_data = json.dumps(latest_match, indent=4)

    start_time = time.time()

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "meta-llama-3.1-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a high-performance CS2 coach. Keep response under 2000 characters"},
            {"role": "user", "content": f"Analyze my last match: {match_data}"},
        ]
    }

    print(f"Sending request to LLM at {llm_url}...")
    try:
        response = requests.post(llm_url, headers=headers, data=json.dumps(payload), timeout=240)

        print(f"Received response with status code: {response.status_code}")

        end_time = time.time()
        duration = end_time - start_time

        if response.status_code == 200:
            ai_response = response.json()
            print(f"AI responded in {duration:.2f} seconds.")
            return ai_response['choices'][0]['message']['content']
        else:
            print(f"LLM Error: {response.text}")
            return f"Coach is lagging! Code: {response.status_code}"

    except requests.exceptions.Timeout:
        print("Timeout: The LLM took too long to respond.")
        return "Coach timed out. Is the local server running?"
    except Exception as e:
        print(f"Critical Error: {e}")
        return "System failure."


def send_webhook(advice, match_time, match_result):
    if not webhook_url:
        print("Skipping webhook: No URL found.")
        return

    color = 3066993 if match_result.lower() == "win" else 15158332

    data = {
        "username": "CS2 AI Coach",
        "embeds": [{
            "title": f"Match Analysis of game played on {match_time}",
            "description": advice[:2000],
            "color": color,
            "footer": {"text": "Powered by Proxmox & Llama 3.1"}
        }]
    }

    request = requests.post(webhook_url, json=data)
    if request.status_code == 200:
        print(f"Webhook sent with status code: {request.status_code}")
    else:
        print(f"Webhook failed with status code: {request.status_code}")


def main():
    print("Starting Leetify AI Coach...")
    match = get_latest_match()
    if match and is_new_match(match['id']):
        result = match['outcome']
        raw_time = match['finished_at']
        dt_obj = datetime.fromisoformat(raw_time.replace('Z', '+00:00'))
        match_time = dt_obj.strftime("%B %d, %H:%M")
        print(f"New match found on {match['map_name']}, sending data to AI Coach...")
        advice = send_data_to_ai(match)
        print(advice)
        send_webhook(advice, match_time, result)
    else:
        print("No new match found")


if __name__ == "__main__":
    main()
