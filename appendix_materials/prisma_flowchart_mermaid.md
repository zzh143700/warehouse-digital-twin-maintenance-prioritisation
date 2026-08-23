# PRISMA-Informed Flow Chart, Final Full-Text Version

Use this version for the dissertation after full-text retrieval and quality appraisal.

```mermaid
flowchart TD
    A["Records identified from databases/platforms<br/>displayed hits: n = 6,416<br/><br/>Scopus, Web of Science, IEEE Xplore,<br/>Google Scholar, ScienceDirect and Warwick Library Search"]
    B["Records captured for pilot screening<br/>n = 100<br/><br/>Records exported/captured into screening CSV"]
    C["Duplicate records removed<br/>n = 15<br/><br/>Normalised-title deduplication"]
    D["Records screened by title and abstract<br/>n = 85"]
    E["Records excluded after title/abstract screening<br/>n = 21<br/><br/>Weak RQ fit or insufficient AI/RUL, DT,<br/>predictive-maintenance or decision-support relevance"]
    F["Reports sought for full-text retrieval<br/>n = 64"]
    G["Reports not retrieved<br/>n = 0"]
    H["Full-text reports retrieved<br/>n = 64<br/><br/>Manual retrieval through Warwick Library,<br/>publisher platforms or open-access routes"]
    I["Full-text reports assessed for eligibility<br/>n = 64"]
    J["Reports excluded after full-text screening<br/>n = 0<br/><br/>Retained literature was stratified by role<br/>rather than excluded at this stage"]
    K["Studies retained for literature review synthesis<br/>n = 64"]
    L["Core evidence<br/>n = 28<br/><br/>Detailed synthesis against the refined RQ"]
    M["Supporting method evidence<br/>n = 20<br/><br/>AI/RUL, DT method, data and architecture support"]
    N["Background/review evidence<br/>n = 16<br/><br/>Definitions, framing and gap identification"]

    A --> B
    B -.-> C
    B --> D
    D -.-> E
    D --> F
    F -.-> G
    F --> H
    H --> I
    I -.-> J
    I --> K
    K --> L
    K --> M
    K --> N

    classDef main fill:#e8f5e9,stroke:#2e7d32,stroke-width:1.5px,color:#102a17;
    classDef removal fill:#fff8e1,stroke:#f9a825,stroke-width:1.5px,color:#4a3500;
    classDef retrieval fill:#fff3e0,stroke:#ef6c00,stroke-width:1.5px,color:#4a2400;
    classDef final fill:#e3f2fd,stroke:#1565c0,stroke-width:1.5px,color:#0d2a4d;
    classDef strata fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1.5px,color:#32104b;

    class A,B,D main;
    class C,E,G,J removal;
    class F,H,I retrieval;
    class K final;
    class L,M,N strata;
```

Suggested caption:

Figure X. PRISMA-informed literature selection flow for the dissertation review. The 6,416 identification count is a displayed-hit count across search platforms and includes overlap; the structured screening set comprised 100 captured records. Following full-text retrieval, all 64 reports were assessed and retained, then stratified into core evidence, supporting method evidence and background/review evidence according to their role in the synthesis.
