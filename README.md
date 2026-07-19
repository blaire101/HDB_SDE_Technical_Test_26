# HDB SDE Technical Test

- Part 1: Developing Data Pipelines （Python ETL pipeline）
- Part 2: Architecting Data Ingestion & Data Exploitation Solution Patterns （AWS）

## Part 1: Developing Data Pipelines

### Part 1 Objective

The pipeline is designed to:

- ingest and combine the required HDB resale source files;
- validate and standardise the data;
- recalculate the remaining lease;
- remove duplicate transactions;
- flag unusual resale prices;
- create the Resale Identifier and SHA-256 hash;
- produce reconciled output datasets.

### Part 1 Processing flow

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

### Part 1 Module structure

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

## Part 2: Data Ingestion Architecting & Data Exploitation Architecting

**AWS Data Ingestion & Data Exploitation Architecture**

### 2.1. AWS Data Ingestion Architecture

## Part 2: Data Ingestion Architecture & Data Exploitation Architecture

### 2.1 AWS Data Ingestion Architecture

#### 2.1.1 Objective

The solution ingests batch files from the public `data.gov.sg` endpoint into Amazon S3.

The design supports:

- files larger than 100 MB;
- processing within private subnets;
- controlled outbound internet access;
- secure storage in Amazon S3;
- automated ETL processing and monitoring.

#### 2.1.2 Processing Flow

#### 2.1.3 Main Components

#### 2.1.4 Network Design

### 2.2 AWS Data Exploitation Architecture

#### 2.2.1 Objective

#### 2.2.2 Processing Flow

#### 2.2.3 Main Components

#### 2.2.4 Network Design

### 2.3 Security, Scalability, and Performance Assumptions

#### 2.3.1 Security

#### 2.3.2 Scalability and Reliability

#### 2.3.3 Performance

#### 2.3.4 General Assumptions


---

- [Data Ingestion Architecture](docs/diagrams/data_ingestion_architecture.png)
- [Data Exploitation Architecture](docs/diagrams/data_exploitation_architecture.png)

