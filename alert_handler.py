import json
import requests
import sys

# Slack Webhook URL (Replace with your Slack webhook URL)
slack_webhook = "https://your-slack-webhook-url"

# Watsonx LLM API URL (Replace with your on-prem Watsonx deployment URL)
llm_url = "https://your-watsonx-url/ml/v1/text/generation?version=2023-05-29"

# LLM API Headers (Ensure you have a valid authentication token)
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer your-auth-token"
}

# Ensure correct arguments are passed
if len(sys.argv) != 7:
    print("Usage: python3 script.py <server> <ip> <disk_percentage> <mount_point> <severity> <description>")
    sys.exit(1)

# Extract arguments
server = sys.argv[1]
ip = sys.argv[2]
disk_percentage = sys.argv[3]
mount = sys.argv[4]
severity = sys.argv[5]
description = sys.argv[6]

# Construct the LLM prompt with Slack formatting guidelines
llm_prompt = f"""
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert DevOps assistant providing troubleshooting steps based on system alerts.
You must return a concise yet informative set of steps per strict Slack guidelines.
Avoid repeating alert details.
Suggest preventive steps only if applicable.

Slack Formatting Guidelines:
1. Use *bold* instead of **bold** for emphasis and headings.
2. Format code blocks using triple backticks (```).
3. Separate sections with double newlines for readability.

<|eot_id|><|start_header_id|>user<|end_header_id|>

An alert has been triggered for high disk usage. Details:
- Server: {server}
- IP: {ip}
- Disk Usage: {disk_percentage}%
- Mount Point: {mount}
- Severity: {severity}
- Description: {description}

Provide step-by-step troubleshooting actions. Ensure responses align with Slack markdown formatting.

<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

# Prepare LLM request payload
body = {
    "input": llm_prompt,
    "parameters": {
        "decoding_method": "greedy",
        "max_new_tokens": 300,
        "repetition_penalty": 1
    },
    "model_id": "meta-llama/llama-3-3-70b-instruct",
    "project_id": "your-project-id"
}

# Request LLM for troubleshooting suggestions
try:
    llm_response = requests.post(llm_url, headers=headers, json=body)
    llm_response.raise_for_status()
    llm_data = llm_response.json()
    
    # Extract AI-generated troubleshooting text
    troubleshooting_text = llm_data.get("results", [{}])[0].get("generated_text", "No suggestions available")

except Exception as e:
    troubleshooting_text = f"Error retrieving AI suggestions: {e}"

# Construct Slack message payload
message = {
    "blocks": [
        {"type": "header", "text": {"type": "plain_text", "text": "🚨 High Disk Usage Alert 🚨"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Server:* {server}\n*IP:* {ip}\n*Disk Usage:* {disk_percentage}%\n*Mount Point:* `{mount}`\n*Severity:* {severity.upper()}\n*Description:* {description}"}},
        {"type": "divider"},
        {"type": "header", "text": {"type": "plain_text", "text": "🤖 AI-Generated Troubleshooting Steps"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": troubleshooting_text}}
    ]
}

# Send Slack notification
response = requests.post(slack_webhook, json=message, headers={"Content-Type": "application/json"})
print(f"Slack Response Code: {response.status_code}")
