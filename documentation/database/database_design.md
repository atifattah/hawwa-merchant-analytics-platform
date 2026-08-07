# Hawwa Database Design


The platform will follow a hybrid architecture:


## Operational Layer

Stores transactional data:

- Orders
- Customers
- Products
- Payments


## Analytical Layer

Optimized for reporting:

- Fact tables
- Dimension tables
- Aggregated metrics


## Data Modeling Approach

Star Schema will be used for analytical workloads.