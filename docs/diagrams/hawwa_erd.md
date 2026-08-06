# Hawwa Entity Relationship Diagram


```mermaid
erDiagram


MERCHANTS ||--o{ STORES : owns

MERCHANTS ||--o{ PRODUCTS : sells

MERCHANTS ||--o{ ORDERS : receives

CUSTOMERS ||--o{ ORDERS : places

ORDERS ||--o{ ORDER_ITEMS : contains

PRODUCTS ||--o{ ORDER_ITEMS : included

ORDERS ||--|| PAYMENTS : has

ORDERS ||--|| SHIPMENTS : has

PRODUCTS ||--o{ REVIEWS : receives

CUSTOMERS ||--o{ REVIEWS : writes

PRODUCTS ||--|| INVENTORY : maintains

MERCHANTS ||--o{ CAMPAIGNS : runs