---
id: "api-petstore-get-user-login"
kind: "api_spec"
title: "PETSTORE GET /user/login"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.161413Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "get"
  - "login"
  - "petstore"
related:
  -
sample_questions:
  - "How do I call GET /user/login on petstore?"
  - "What parameters are required for GET /user/login?"
  - "What errors can GET /user/login return?"
---

# PETSTORE GET /user/login

## Method
- `GET`

## Path
- `/user/login`

## Summary
Logs user into the system.

## Parameters
- `username` (query, string, optional)
- `password` (query, string, optional)

## Auth
- not specified

## Error Model
- `400`: Invalid username/password supplied

## Examples
- no explicit examples
