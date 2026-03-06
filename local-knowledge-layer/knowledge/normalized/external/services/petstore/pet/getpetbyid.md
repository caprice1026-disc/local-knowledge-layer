---
id: "api-petstore-get-pet-petid"
kind: "api_spec"
title: "PETSTORE GET /pet/{petId}"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.132372Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "get"
  - "pet"
  - "petstore"
related:
  -
sample_questions:
  - "How do I call GET /pet/{petId} on petstore?"
  - "What parameters are required for GET /pet/{petId}?"
  - "What errors can GET /pet/{petId} return?"
---

# PETSTORE GET /pet/{petId}

## Method
- `GET`

## Path
- `/pet/{petId}`

## Summary
Find pet by ID.

## Parameters
- `petId` (path, integer, required)

## Auth
- api_key
- petstore_auth: write:pets, read:pets

## Error Model
- `400`: Invalid ID supplied
- `404`: Pet not found

## Examples
- no explicit examples
