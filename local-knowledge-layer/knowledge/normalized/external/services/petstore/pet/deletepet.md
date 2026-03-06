---
id: "api-petstore-delete-pet-petid"
kind: "api_spec"
title: "PETSTORE DELETE /pet/{petId}"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.136212Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "delete"
  - "pet"
  - "petstore"
related:
  -
sample_questions:
  - "How do I call DELETE /pet/{petId} on petstore?"
  - "What parameters are required for DELETE /pet/{petId}?"
  - "What errors can DELETE /pet/{petId} return?"
---

# PETSTORE DELETE /pet/{petId}

## Method
- `DELETE`

## Path
- `/pet/{petId}`

## Summary
Deletes a pet.

## Parameters
- `api_key` (header, string, optional)
- `petId` (path, integer, required)

## Auth
- petstore_auth: write:pets, read:pets

## Error Model
- `400`: Invalid pet value

## Examples
- no explicit examples
