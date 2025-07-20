#!/usr/bin/env bash

# Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1 