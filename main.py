import sys

import requests
import os
import json
import time
import logging as log
from datetime import datetime

env = os.environ.get

steam_id = env("steam_id")
base_url = env("leetify_url")
leetify_url = f"{base_url}{steam_id}"
llm_url = env("llm_url")
state_file = env("state_file")
webhook_url = env("webhook_url")

if not os.path.exists("logs"):
    os.makedirs("logs")

log.basicConfig(
    level=log.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        log.StreamHandler(),
        log.FileHandler("logs/coach.log")
    ]
)


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
        log.error("Error! No SteamID found in environment variables")
        return None

    for attempt in range(3):
        try:
            response = requests.get(leetify_url, timeout=10)

            if response.status_code != 200:
                log.error(f"Failed! Error code: {response.status_code}")
                time.sleep(2 ** attempt)
                continue

            data = response.json()
            matches = data.get('recent_matches', [])

            if not matches:
                log.warning("No matches found in API response")
                time.sleep(2 ** attempt)
                continue

            return matches[0]

        except requests.exceptions.RequestException as e:
            log.error(f"Request failed: {e}")
            time.sleep(2 ** attempt)

    log.error("Failed to get latest match after retries.")
    sys.exit(1)


def send_data_to_ai(latest_match):
    log.info(f"Preparing data for match on {latest_match['map_name']}...")
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

    log.info(f"Sending request to LLM at {llm_url}...")
    for attempt in range(3):
        try:
            response = requests.post(llm_url, headers=headers, data=json.dumps(payload), timeout=240)

            log.info(f"Received response with status code: {response.status_code}")

            end_time = time.time()
            duration = end_time - start_time

            if response.status_code == 200:
                ai_response = response.json()
                log.info(f"AI responded in {duration:.2f} seconds.")
                return ai_response['choices'][0]['message']['content']
            else:
                log.error(f"LLM Error: {response.text}")
                time.sleep(2 ** attempt)

        except requests.exceptions.Timeout:
            log.error("Timeout: The LLM took too long to respond.")
            time.sleep(2 ** attempt)
        except Exception as e:
            log.error(f"Critical Error: {e}")
            time.sleep(2 ** attempt)
    log.error("Critical Error")
    sys.exit(1)


def send_webhook(advice, match_time, match_result):
    if not webhook_url:
        log.error("Skipping webhook: No URL found.")
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
    for attempt in range(3):
        try:
            response = requests.post(webhook_url, json=data, timeout=10)
            if 200 <= response.status_code < 300:
                log.info(f"Webhook sent with status code: {response.status_code}")
                return
            else:
                log.error(f"Webhook failed with status code: {response.status_code}")
                time.sleep(2 ** attempt)
        except requests.exceptions.Timeout:
            log.error("Timeout: The webhook took too long to respond.")
            time.sleep(2 ** attempt)
        except Exception as e:
            log.error(f"Webhook Error: {e}")
            time.sleep(2 ** attempt)
    log.error("All webhook retry attempts failed.")
    sys.exit(1)



def main():
    log.info("Starting Leetify AI Coach...")
    match = get_latest_match()
    if match and is_new_match(match['id']):
        result = match['outcome']
        raw_time = match['finished_at']
        dt_obj = datetime.fromisoformat(raw_time.replace('Z', '+00:00'))
        match_time = dt_obj.strftime("%B %d, %H:%M")
        log.info(f"New match found on {match['map_name']}, sending data to AI Coach...")
        advice = send_data_to_ai(match)
        send_webhook(advice, match_time, result)
    else:
        log.info("No new match found")


if __name__ == "__main__":
    main()
