---
id: "api-petstore-post-pet-petid-uploadimage"
kind: "api_spec"
title: "PETSTORE POST /pet/{petId}/uploadImage"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.138412Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "petstore"
  - "post"
  - "uploadimage"
related:
  -
sample_questions:
  - "How do I call POST /pet/{petId}/uploadImage on petstore?"
  - "What parameters are required for POST /pet/{petId}/uploadImage?"
  - "What errors can POST /pet/{petId}/uploadImage return?"
---

# PETSTORE POST /pet/{petId}/uploadImage

## Method
- `POST`

## Path
- `/pet/{petId}/uploadImage`

## Summary
Uploads an image.

## Parameters
- `petId` (path, integer, required)
- `additionalMetadata` (query, string, optional)

## Auth
- petstore_auth: write:pets, read:pets

## Error Model
- `400`: No file uploaded
- `404`: Pet not found

## Examples
- no explicit examples
