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
* **Easy to start:** Just add URL of Rate limiter at the beginning and it works.
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
           "url": "url1"
       },
         "rate_limit": {
           "interval": 1,  // in seconds
           "RPD": 10,       // Requests Per Day
           "add_random": true   
         }
       },
       {
         "identifier": {
           "url": "url1",
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
|--------------|----------------------------------------------------------------------------------------------------------------|-------|
| `identifier` | A unique identifier for the API source. Identifier serializes to a key.                                        | `dict` |
| `rate_limit` | An object defining the rate limiting parameters.                                                               | `object` |
| `interval`   | Interval between requests in order to do not reach "Too many reqeusts"                                         | `number` |
| `RPD`        | The maximum number of requests allowed within the specified `interval`.                                        | `integer` |
| `add_random` | Adds random number from 0 to 1 to interval.<br/>Prevents from ban, when external API conrols time between requests. | `bool` |

### Identifier Options

| Key          | Description                                                      | Data Type |
|--------------|------------------------------------------------------------------|-----------|
| `url`        | Required. URL.                                                   | `string`  |
| `method`     | Optional. HTTP method. Default `"ANY"`                           | `string`  |
| `extra`      | Optional. Can be specified for special identifier cases.<br/>Default`""` | `string`  |

### Priority Options

Priority is passed in headers by `x-priority` key. Priority type is `str` (must represent an `int` value).
The value is casted to an integer using `int(value)`.

## Request Example

Assume we have Some request in our code:
```bash

curl -X POST "{URL}" \
  -H "Content-Type: application/json" \
  -d "{'msg': 'Hello world'}"
 
```

To start use Rate Limiter just add RATELIMITER_URL before URL:
```bash

curl -X POST "{RATELIMITER_URL}{URL}" \
  -H "Content-Type: application/json" \
  -d "{'msg': 'Hello world'}"
 
```

To pass priority argument, just add it to headers:
```bash

curl -X POST "{RATELIMITER_URL}{URL}" \
  -H "Content-Type: application/json" \
  -H "x-priority: '5'" \
  -d "{'msg': 'Hello world'}"
 
```

## Notes

**1.** Any JSON serializable dict can be used as an identifier.

**2.** Add identifiers carefully. Suppose there is only api config with `identifier.url` equals to `url1` and you make request
to `url2`, that is a child of `url1` (for example  url1 = 'https://examplse.com', url2 = 'https://examplse.com/some_endpoint').
In that case Rate limiter will use rate limits of api config with identifier equals to `url1`. Think twice to add another identifier.

