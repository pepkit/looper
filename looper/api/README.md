# Looper HTTP API

## Overview

This API provides an HTTP interface for running the `looper` commands, allowing users to interact with Looper via HTTP requests.

## Usage
### Running the API
To run the API, execute the following command:
```bash
cd looper/api
uvicorn main:app --reload
```
### Example API Usage
To run the `looper run` command through the HTTP API, you can use the following curl command:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"run": {}, "looper_config": ".looper.yaml"}' "http://127.0.0.1:8000"
```
with the project files in the same `looper/api` folder.

This example sends a JSON payload with the `run` and `looper_config` parameters to the `/` endpoint.

## API Documentation
The API documentation is automatically generated and can be accessed in your web browser:

Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

Explore the API documentation to understand available endpoints, request parameters, and response formats.
