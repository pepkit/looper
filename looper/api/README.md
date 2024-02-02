# Looper HTTP API

## Overview

This API provides an HTTP interface for running the `looper` commands, allowing users to interact with Looper via HTTP requests.

## Usage
### Running the server
Run the app:
```bash
looper-serve [--host <host IP address>] [--port <port>]
```

> [!NOTE]
This assumes that all files specified in the arguments are available on the file system of the machine that is running the HTTP API server. Best make sure you use absolute file paths in all `looper` YAML configuration files.

### Sending requests
To test this, you can clone the [`hello_looper`](https://github.com/pepkit/hello_looper) repository and then run (for example) the following in a second terminal:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"run": {"time_delay": 5}, "looper_config": "/path/to/hello_looper/.looper.yaml"}' "http://127.0.0.1:8000"
```
This will return a six-letter job ID, say `abc123`. Then get the result / output of the run with
```bash
curl -X GET -v localhost:8000/status/abc123
```
For better visualization / readability, you can post-process the output by piping it to `jq` (` | jq -r .console_output`).

## API Documentation
The API documentation is automatically generated and can be accessed in your web browser:

Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

Explore the API documentation to understand available endpoints, request parameters, and response formats.
