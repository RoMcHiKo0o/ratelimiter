# ratelimiter

## Project Overview

This repository contains a Python-based rate limiter designed to manage and control the rate at which API requests are
made to various sources. It utilizes asynchronous programming with `asyncio` and the `FastAPI` framework for handling
API interactions. The project aims to provide a robust and configurable solution for preventing rate limiting issues
when interacting with external APIs.

## Motivation

In many systems, there can be multiple independent sources that send requests to various external APIs — each of which
may have its own rate limits.
Without proper coordination, it becomes difficult to ensure that these limits are respected, and some parts of the
system might accidentally exceed them.

The goal of this project is to build a centralized layer that all outgoing requests pass through.
This layer monitors and controls request flow to external APIs, ensuring that each API’s rate limits are obeyed while
allowing multiple internal sources to work safely and efficiently in parallel.

## Key Features & Benefits

* **Asynchronous Request Handling:** Utilizes `asyncio` for efficient and non-blocking API request management.
* **Configurable Rate Limiting:** Defines rate limits (requests per duration) for each API based on configuration files.
* **API Management:** Manages multiple API instances with individual rate limiting settings.
* **Dynamic Configuration Loading:** Loads API configurations from a JSON file, allowing for easy updates and additions.
* **Centralized Logging:** Implements logging for debugging and monitoring purposes.
* **FastAPI Integration:** Uses FastAPI framework to provide endpoints.
* **Prioritized Requests:** Allows marking requests with priority levels to ensure faster processing.

## Usage Examples & API Documentation

1. **Running the application**

   ```bash
   uvicorn main:app
   ```
   Or run the `run.bat` batch file to start the application.

2. **Configuration File (apis.json) Example:**

   ```jsonc
   {
     "sources": [
       {
         "identifier": {
           "url": "api1"
       },
         "rate_limit": {
           "interval": 1,  // in seconds
           "RPD": 10,       // Requests Per Day
           "add_random": true   
         }
       },
       {
         "identifier": {
           "url": "api2",
           "method": "GET"
       },
         "rate_limit": {
           "interval": 0.5,
           "RPD": -1     // No limit per day, can be not passed with the same behaivour
         }
       }
     ]
   }
   ```

3. **Accessing APIs**:

   After the application is running, you can make requests to your FastAPI API endpoints which use `APIManager` to
   interact with external APIs according to their defined rate limits.

## Configuration Options

The project's behavior can be configured using the `apis.json` file. Here's a breakdown of the available options:

| Key          | Description                                                                                                    | Data Type |
|--------------|----------------------------------------------------------------------------------------------------------------|--------|
| `identifier` | A unique identifier for the API source.                                                                        | `string` |
| `rate_limit` | An object defining the rate limiting parameters.                                                               | `object` |
| `interval`   | Interval between requests in order to do not reach "Too many reqeusts"                                         | `number` |
| `RPD`        | The maximum number of requests allowed within the specified `interval`.                                        | `integer` |
| `add_random` | Adds random number from 0 to 1 to interval.<br/>Prevents from ban, when external API conrols time between requests. | `bool` |

## Request Example

```bash

curl -X POST "http://127.0.0.1:8000/" \
  -H "Content-Type: application/json" \
  -d "{
    'identifier': {
        'url': 'https://www.example.com/endpoint',
        'method': 'POST'
    },
    'request': {
        'url': 'https://www.example.com/endpoint',
        'method': 'POST',
        'headers': {'Content-Type': 'application/json'}
        'params': {'id': 123},
        'json': {
            'msg': 'Hello world'
        }
    },
    'priority': 3
  }" 
```

## Request Options
`request`: Just data for HTTP request

`priority`: Default priority is `0`. Greater is more prioritized.

## Notes

Anything JSON serializable can be used as an identifier. You can pass not only json with a url, method, etc., but
anything. Better not pass None-like objects as identifier.

