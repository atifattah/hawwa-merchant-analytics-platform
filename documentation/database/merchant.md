# Merchant Table

Purpose

Stores merchant master information.

Primary Key

merchant_id

Business Rules

- One merchant can own multiple stores.
- One merchant can run multiple campaigns.
- One merchant has one active subscription.

Relationships

Merchant → Stores

Merchant → Campaigns

Merchant → Subscription