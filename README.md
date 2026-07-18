# HDB SDE Technical Test

- Part 1: Developing Data Pipelines （Python ETL pipeline）
- Part 2: Architecting Data Ingestion & Data Exploitation Solution Patterns （AWS）

## Part 1: Developing Data Pipelines

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
        D[Validate and Standardize]
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

        H --> I --> J --> K --> L
    end

    C --> D
    G --> H

    D -. Invalid records .-> X1[Validation Failed Dataset]
    F -. Duplicate records .-> X2[Duplicate Failed Dataset]

    X1 --> X[Failed Dataset]
    X2 --> X

    G -. Price anomalies .-> Y[Review Dataset]

    classDef ingest fill:#EAF2FF,stroke:#2563EB,stroke-width:2px,color:#111827;
    classDef quality fill:#FFF4E5,stroke:#D97706,stroke-width:2px,color:#111827;
    classDef output fill:#ECFDF3,stroke:#059669,stroke-width:2px,color:#111827;
    classDef failed fill:#FEECEC,stroke:#DC2626,stroke-width:2px,color:#7F1D1D;
    classDef review fill:#F3EFFE,stroke:#7C3AED,stroke-width:2px,color:#4C1D95;

    class A,B,C ingest;
    class D,E,F,G quality;
    class H,I,J,K,L output;
    class X1,X2,X failed;
    class Y review;
```

### Part 1 module structure

```text
src/hdb_pipeline/
├── main.py             # command-line entry point
├── config.py           # pipeline configuration
├── ingestion.py        # source discovery, extraction and schema union
├── data_quality.py     # profiling, validation, lease, deduplication and anomaly detection
├── transformation.py   # Resale Identifier and SHA-256 hashing
├── output.py           # output datasets and run manifest
└── pipeline.py         # end-to-end ETL orchestration
```

### Part 1 Quick start

#### Option 1: Conda

The following commands assume that Conda is already installed.

```bash
conda create -n g2hdb python=3.10
conda activate g2hdb
```

#### Option 2: Python venv

Use Python's built-in virtual environment if Conda is not available.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### Run the Pipeline

Run the following command from the project root:

```bash
PYTHONPATH=src python -m hdb_pipeline.main \
  --input-path data/input/ResaleFlatPrices.zip \
  --output-dir output \
  --as-of-date 2026-07-18
```

### Run the Notebook

```bash
jupyter notebook notebooks/hdb_resale_pipeline.ipynb
```

### Run Tests

```bash
PYTHONPATH=src pytest -q
```

## Part 2: Architecting Data Ingestion & Data Exploitation Solution Patterns

**AWS Data Ingestion & Data Exploitation Architecture**

- [Part 2 AWS Architecture and Assumptions](docs/PART2_AWS_ARCHITECTURE.md)
- [Data Ingestion Architecture](docs/diagrams/data_ingestion_architecture.png)
- [Data Exploitation Architecture](docs/diagrams/data_exploitation_architecture.png)

