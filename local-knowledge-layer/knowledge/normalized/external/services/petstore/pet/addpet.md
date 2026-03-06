---
id: "api-petstore-post-pet"
kind: "api_spec"
title: "PETSTORE POST /pet"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.124095Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "pet"
  - "petstore"
  - "post"
related:
  -
sample_questions:
  - "How do I call POST /pet on petstore?"
  - "What parameters are required for POST /pet?"
  - "What errors can POST /pet return?"
---

# PETSTORE POST /pet

## Method
- `POST`

## Path
- `/pet`

## Summary
Add a new pet to the store.

## Parameters
- none

## Auth
- petstore_auth: write:pets, read:pets

## Error Model
- `400`: Invalid input
- `422`: Validation exception

## Examples
- no explicit examples
