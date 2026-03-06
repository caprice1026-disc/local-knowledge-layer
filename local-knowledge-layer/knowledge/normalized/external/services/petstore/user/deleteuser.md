---
id: "api-petstore-delete-user-username"
kind: "api_spec"
title: "PETSTORE DELETE /user/{username}"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.173102Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "delete"
  - "petstore"
  - "user"
related:
  -
sample_questions:
  - "How do I call DELETE /user/{username} on petstore?"
  - "What parameters are required for DELETE /user/{username}?"
  - "What errors can DELETE /user/{username} return?"
---

# PETSTORE DELETE /user/{username}

## Method
- `DELETE`

## Path
- `/user/{username}`

## Summary
Delete user resource.

## Parameters
- `username` (path, string, required)

## Auth
- not specified

## Error Model
- `400`: Invalid username supplied
- `404`: User not found

## Examples
- no explicit examples
