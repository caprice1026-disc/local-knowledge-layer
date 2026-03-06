---
id: "api-petstore-get-pet-findbytags"
kind: "api_spec"
title: "PETSTORE GET /pet/findByTags"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.129220Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "findbytags"
  - "get"
  - "petstore"
related:
  -
sample_questions:
  - "How do I call GET /pet/findByTags on petstore?"
  - "What parameters are required for GET /pet/findByTags?"
  - "What errors can GET /pet/findByTags return?"
---

# PETSTORE GET /pet/findByTags

## Method
- `GET`

## Path
- `/pet/findByTags`

## Summary
Finds Pets by tags.

## Parameters
- `tags` (query, array, required)

## Auth
- petstore_auth: write:pets, read:pets

## Error Model
- `400`: Invalid tag value

## Examples
- no explicit examples
