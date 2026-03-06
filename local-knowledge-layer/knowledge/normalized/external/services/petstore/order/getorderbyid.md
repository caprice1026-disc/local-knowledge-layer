---
id: "api-petstore-get-store-order-orderid"
kind: "api_spec"
title: "PETSTORE GET /store/order/{orderId}"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.149220Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "get"
  - "order"
  - "petstore"
related:
  -
sample_questions:
  - "How do I call GET /store/order/{orderId} on petstore?"
  - "What parameters are required for GET /store/order/{orderId}?"
  - "What errors can GET /store/order/{orderId} return?"
---

# PETSTORE GET /store/order/{orderId}

## Method
- `GET`

## Path
- `/store/order/{orderId}`

## Summary
Find purchase order by ID.

## Parameters
- `orderId` (path, integer, required)

## Auth
- not specified

## Error Model
- `400`: Invalid ID supplied
- `404`: Order not found

## Examples
- no explicit examples
