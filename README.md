# HDB Senior Data Engineer Technical Test

- Part 1: Python ETL pipeline
- Part 2: AWS architecture design

## Part 1 - Python ETL pipeline

### Part 1 processing flow

```mermaid
flowchart TD
    A[Read Source Files]
    B[Combine Files and Keep 2012-2016 Records]
    C[Check Data Structure and Values]
    D[Validate Required Fields]
    E[Recalculate Remaining Lease]
    F[Remove Duplicate Transactions]
    G[Identify Unusual Resale Prices]
    H[Create Cleaned Dataset]
    I[Create Resale Identifier]
    J[Create Transformed Dataset]
    K[Hash Resale Identifier with SHA-256]
    L[Create Hashed Dataset]

    X[Invalid and Duplicate Records]
    Y[Price Records for Manual Review]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    I --> K
    K --> L

    D -. Invalid records .-> X
    F -. Lower-price duplicates .-> X
    G -. Unusual prices .-> Y

    classDef input fill:#EAF2FF,stroke:#2563EB,stroke-width:2px,color:#111827;
    classDef check fill:#FFF4E5,stroke:#D97706,stroke-width:2px,color:#111827;
    classDef output fill:#ECFDF3,stroke:#059669,stroke-width:2px,color:#111827;
    classDef failed fill:#FEECEC,stroke:#DC2626,stroke-width:2px,color:#7F1D1D;
    classDef review fill:#F3EFFE,stroke:#7C3AED,stroke-width:2px,color:#4C1D95;

    class A,B,C input;
    class D,E,F,G check;
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
