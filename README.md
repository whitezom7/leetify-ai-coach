# leetify-ai-coach

## An automated performance analysis pipeline that turns CS2 match data into actionable AI coaching.

### Overview

This project is a DevOps-focused automation tool designed to bridge the gap between raw match statistics and actual skill improvement. It monitors a player's Leetify profile, detects new matches, and uses a Large Language Model (LLM) to provide personalized, constructive feedback delivered directly to Discord.
### Tech Stack

    Language: Python 3.x

    Data Source: Leetify Public API

    Intelligence: OpenAI / Gemini API (LLM Integration)

    Delivery: Discord Webhooks

    Infrastructure: Docker (Targeted for Proxmox/Home Lab deployment)

### Key Features

    Automated Polling: Periodically checks for new match uploads.

    Smart Analysis: Prompts an AI "Coach" to analyze specific KPIs like Utility Usage, Flash Assistance, and Trade Efficiency.

    Instant Feedback: Sends a formatted summary and "Top 3 Improvement Tips" to a private Discord channel.