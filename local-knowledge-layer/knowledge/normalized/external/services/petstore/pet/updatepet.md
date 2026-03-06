---
id: "api-petstore-put-pet"
kind: "api_spec"
title: "PETSTORE PUT /pet"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.118829Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "pet"
  - "petstore"
  - "put"
related:
  -
sample_questions:
  - "How do I call PUT /pet on petstore?"
  - "What parameters are required for PUT /pet?"
  - "What errors can PUT /pet return?"
---

# PETSTORE PUT /pet

## Method
- `PUT`

## Path
- `/pet`

## Summary
Update an existing pet.

## Parameters
- none

## Auth
- petstore_auth: write:pets, read:pets

## Error Model
- `400`: Invalid ID supplied
- `404`: Pet not found
- `422`: Validation exception

## Examples
- no explicit examples
