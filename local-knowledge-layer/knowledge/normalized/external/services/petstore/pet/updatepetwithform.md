---
id: "api-petstore-post-pet-petid"
kind: "api_spec"
title: "PETSTORE POST /pet/{petId}"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.134741Z"
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
  - "How do I call POST /pet/{petId} on petstore?"
  - "What parameters are required for POST /pet/{petId}?"
  - "What errors can POST /pet/{petId} return?"
---

# PETSTORE POST /pet/{petId}

## Method
- `POST`

## Path
- `/pet/{petId}`

## Summary
Updates a pet in the store with form data.

## Parameters
- `petId` (path, integer, required)
- `name` (query, string, optional)
- `status` (query, string, optional)

## Auth
- petstore_auth: write:pets, read:pets

## Error Model
- `400`: Invalid input

## Examples
- no explicit examples
