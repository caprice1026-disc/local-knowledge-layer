---
id: "api-petstore-delete-store-order-orderid"
kind: "api_spec"
title: "PETSTORE DELETE /store/order/{orderId}"
project: ""
service: "petstore"
source_url: "https://petstore3.swagger.io/api/v3/openapi.json"
source_type: "json"
last_checked: "2026-03-06T12:06:22.151709Z"
freshness: "volatile"
version_hint: "1.0.27"
tags:
  - "api_spec"
  - "delete"
  - "order"
  - "petstore"
related:
  -
sample_questions:
  - "How do I call DELETE /store/order/{orderId} on petstore?"
  - "What parameters are required for DELETE /store/order/{orderId}?"
  - "What errors can DELETE /store/order/{orderId} return?"
---

# PETSTORE DELETE /store/order/{orderId}

## Method
- `DELETE`

## Path
- `/store/order/{orderId}`

## Summary
Delete purchase order by identifier.

## Parameters
- `orderId` (path, integer, required)

## Auth
- not specified

## Error Model
- `400`: Invalid ID supplied
- `404`: Order not found

## Examples
- no explicit examples
