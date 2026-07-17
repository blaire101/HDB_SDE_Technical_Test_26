# HDB SDE Technical Test

- Part 1: Python ETL pipeline
- Part 2: AWS architecture design

## Part 1 - Python ETL pipeline

### Part 1 processing flow

```mermaid
flowchart TD
    subgraph P1[1. Ingest and Prepare]
        A[Read Source Files]
        B[Combine and Filter Records]
        C[Profile Data Quality]
        A --> B --> C
    end

    subgraph P2[2. Clean and Validate]
        D[Validate Required Fields]
        E[Recalculate Remaining Lease]
        F[Remove Duplicate Transactions]
        G[Flag Unusual Prices]
        D --> E --> F --> G
    end

    subgraph P3[3. Create Outputs]
        H[Cleaned Dataset]
        I[Create Resale Identifier]
        J[Transformed Dataset]
        K[Apply SHA-256 Hash]
        L[Hashed Dataset]
        H --> I
        I --> J
        I --> K --> L
    end

    C --> D
    G --> H

    D -. Invalid records .-> X[Failed Dataset]
    F -. Duplicate records .-> X
    G -. Price anomalies .-> Y[Review Dataset]

    classDef ingest fill:#EAF2FF,stroke:#2563EB,stroke-width:2px,color:#111827;
    classDef quality fill:#FFF4E5,stroke:#D97706,stroke-width:2px,color:#111827;
    classDef output fill:#ECFDF3,stroke:#059669,stroke-width:2px,color:#111827;
    classDef failed fill:#FEECEC,stroke:#DC2626,stroke-width:2px,color:#7F1D1D;
    classDef review fill:#F3EFFE,stroke:#7C3AED,stroke-width:2px,color:#4C1D95;

    class A,B,C ingest;
    class D,E,F,G quality;
    class H,I,J,K,L output;
    class X failed;
    class Y review;
```

### Part 1 module structure

```text
src/hdb_pipeline/
├── main.py             # main() and command-line arguments
├── config.py          # central pipeline settings
├── ingestion.py       # ZIP/directory/CSV discovery, raw copy, schema union
├── quality.py         # profiling, validation, lease, deduplication, anomaly flags
├── transformation.py  # Resale Identifier and SHA-256
├── output.py          # mandatory outputs and run manifest
└── pipeline.py        # concise end-to-end ETL orchestration
```

### Part 1 Quick start

```bash
conda create -n g2hdb python=3.10
conda activate g2hdb
```

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

PYTHONPATH=src python -m hdb_pipeline.main \
  --input-path data/input/ResaleFlatPrices.zip \
  --output-dir output \
  --as-of-date 2026-07-17
```

Run the automated tests:

```bash
PYTHONPATH=src pytest -q
```


## Part 2 — AWS Data Ingestion & Data Exploitation Architecture
