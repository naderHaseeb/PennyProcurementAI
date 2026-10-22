# Penny Procurement AI

AI Engineer Internship Assessment

## Overview
A conversational procurement analytics assistant using California
government purchasing records from 2012–2015.

## Technologies
Python, FastAPI, MongoDB, LangGraph, Ollama (Qwen2.5 Coder 3B),
Pandas, HTML, CSS, JavaScript.

## Architecture
Frontend → FastAPI → Procurement query handler → MongoDB → Answer

Supported common analytical questions use predefined, validated
MongoDB aggregations for reliability. Other questions are routed
through a LangGraph agent that uses Ollama to generate queries,
followed by validation and execution.

## Dataset
Source: https://www.kaggle.com/datasets/sohier/large-purchases-by-the-state-of-ca

Imported records: 346,018.

Download the CSV separately and place it in data/raw/.

## Installation
Create a Python virtual environment and activate it.

Install Python dependencies:
    python -m pip install -r requirements.txt

Configure .env using .env.example.
Start local MongoDB and Ollama.
Download the Ollama model:
    ollama pull qwen2.5-coder:3b

Import records:
    python scripts/import_data.py

## Run Backend
    python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

## Run Frontend
    python3 -m http.server 5500 --directory frontend --bind 127.0.0.1

Open http://127.0.0.1:5500/index.html

## Evaluation
Run existing validation tests:
    python -m pytest tests/ -v

Successful API examples:
- January 2014: 4,557 unique purchase orders.
- Top five suppliers by recorded net spending.
- Highest spending quarter in 2014: Q2.

These examples have passed API execution. This does not
establish accuracy for all possible questions.

## Limitations
The local language model sometimes generates unsupported queries.
The query validator supports a limited aggregation subset.
The application is a localhost prototype, not production-hardened.
Database access should be restricted to read-only for deployment.
