flowchart LR

A[Merchant Simulator]

B[Operational Database]

C[ETL Pipeline]

D[Data Warehouse]

E[Semantic Layer]

F[Analytics Engine]

G[FastAPI]

H[Streamlit Dashboard]

I[Power BI]


A --> B

B --> C

C --> D

D --> E

E --> F

F --> G

F --> H

D --> I