---
id: "api-petstore-get-pet-findbystatus"
kind: "api_spec"
title: "PETSTORE GET /pet/findByStatus"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.126379Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "findbystatus"
  - "get"
  - "petstore"
related:
  -
sample_questions:
  - "How do I call GET /pet/findByStatus on petstore?"
  - "What parameters are required for GET /pet/findByStatus?"
  - "What errors can GET /pet/findByStatus return?"
---

# PETSTORE GET /pet/findByStatus

## Method
- `GET`

## Path
- `/pet/findByStatus`

## Summary
Finds Pets by status.

## Parameters
- `status` (query, string, required)

## Auth
- petstore_auth: write:pets, read:pets

## Error Model
- `400`: Invalid status value

## Examples
- no explicit examples
