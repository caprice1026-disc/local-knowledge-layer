---
id: "api-petstore-get-user-username"
kind: "api_spec"
title: "PETSTORE GET /user/{username}"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.167902Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "get"
  - "petstore"
  - "user"
related:
  -
sample_questions:
  - "How do I call GET /user/{username} on petstore?"
  - "What parameters are required for GET /user/{username}?"
  - "What errors can GET /user/{username} return?"
---

# PETSTORE GET /user/{username}

## Method
- `GET`

## Path
- `/user/{username}`

## Summary
Get user by user name.

## Parameters
- `username` (path, string, required)

## Auth
- not specified

## Error Model
- `400`: Invalid username supplied
- `404`: User not found

## Examples
- no explicit examples
