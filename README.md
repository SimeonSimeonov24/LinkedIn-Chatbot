# LinkedIn-Chatbot

## About The Project

Goal: Find a suitable job based on your skills and interests (in a specific region) or identify specific job requirements - using LinkedIn data.

### Installation

```
git clone https://github.com/SimeonSimeonov24/LinkedIn-Chatbot.git
```

## Getting Started

1. Make .env and fill missing variables

   ```bash
   cp .env.example .env
   ```

2. Get data from [linkedin-job-postings](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) and only move postings.csv inside the data folder
3. Start Docker Desktop and after that run:

   ```
   docker-compose down -v
   docker-compose up -d
   docker ps
   ```

4. Install requirements

   ```
   pip install -r requirements.txt
   ```

5. Run `data_processing.py`

## Run

Run `main.py`
