# Digital-Twin-Inspired Warehouse Maintenance Decision-Support Simulation Protocol

**Initial specification locked:** 20 July 2026  
**Supervisor-confirmed revision:** 4 August 2026  
**Status:** Revised proof-of-concept protocol. All criteria and sensitivity alternatives below are declared before the revised run.

## 1. Methodological description and transfer boundary

The study is a **digital-twin-inspired maintenance decision-support simulation**. It is not a live digital twin, a warehouse case study or an operational intervention.

The Gradient Boosting model predicts RUL for C-MAPSS FD001 turbofan engines. Model MAE and RMSE therefore apply only to C-MAPSS. When the numerical endpoint predictions enter the warehouse simulation, they are renamed **surrogate RUL inputs**. They represent controlled degradation-state values for testing the prioritisation method; they are not predictions of remaining life for conveyors, lifts, mobile robots or packing equipment.

The five warehouse records are researcher-constructed virtual asset instances. Their scores are not C-MAPSS variables or measured warehouse facts. Literature and process logic inform the dimensions, while the exact 1--5 values remain author-assigned scenario parameters.

## 2. Virtual assets, criteria and assignment rationale

| ID | Asset role | Configuration criterion | Criticality | Criticality justification | Assumed capacity loss | Throughput score | Severity | Severity justification |
|---|---|---|---:|---|---:|---:|---:|---|
| A1 | Inbound conveyor motor | Important inbound path with short buffering and a limited temporary workaround | 4 | Major process dependency, but limited short-term continuity remains | 40% | 3 | 3 | Moderate disruption and recovery exposure without a severe safety or continuity assumption |
| A2 | Sortation conveyor drive | Main sortation route with no full-capacity bypass | 5 | System-critical route with no effective substitute | 80% | 5 | 4 | Serious service and business-continuity exposure, but not the maximum catastrophic category |
| A3 | Vertical lift motor | Limited vertical redundancy and difficult recovery | 4 | Major process dependency with restricted redundancy | 55% | 4 | 4 | Difficult recovery and serious service or damage exposure |
| A4 | AGV/shuttle drive unit | One unit within a multi-vehicle fleet; workload can be redistributed | 2 | Strong fleet redundancy limits the interruption | 15% | 2 | 2 | Minor local service and recovery effect |
| A5 | Packing-station roller motor | One of two packing paths; partial capacity remains available | 3 | An important process is affected, but a workable alternative remains | 35% | 3 | 2 | Partial capacity remains and the assumed non-throughput effect is minor |

## 3. Literature-informed 1--5 score criteria

The dimensions are informed by FMEA/FMECA principles: the analysis makes failure consequences, severity and system criticality explicit before prioritisation. The simulation does **not** implement a standard FMEA or FMECA worksheet, risk-priority number or probability-of-failure model. IEC 60812:2018 informs the logic but does not prescribe the exact scores below.

### 3.1 Criticality

- **1:** local auxiliary role with an immediately available substitute;
- **2:** minor local interruption with strong redundancy;
- **3:** one important process is affected, but a workable alternative exists;
- **4:** major process dependency with limited redundancy or difficult recovery;
- **5:** system-critical single point of failure with no effective substitute.

### 3.2 Throughput impact

- **1:** less than 10% assumed capacity loss;
- **2:** 10--24%;
- **3:** 25--49%;
- **4:** 50--74%;
- **5:** 75% or more.

The capacity-loss percentages are scenario inputs used to make the throughput score auditable. They are not outputs from a discrete-event simulation or observed operational losses.

### 3.3 Consequence severity

- **1:** negligible non-throughput effect and straightforward recovery;
- **2:** minor damage, service or cost effect;
- **3:** moderate disruption or recovery requirement;
- **4:** serious safety, damage, service, recovery or cost exposure;
- **5:** severe safety, regulatory, damage or business-continuity consequence.

### 3.4 Score-assignment sensitivity criterion

Every author-assigned criticality, throughput and severity score is tested one adjacent anchor lower and one adjacent anchor higher, bounded by the 1--5 scale. For example, a base score of 3 is tested at 2 and 4, while a base score of 5 is tested only at 4. This one-step rule represents uncertainty about classification at an adjacent rubric boundary without inventing a new measurement scale. It is applied both to the fixed base assignment and across the repeated seeded RUL assignments.

## 4. Controlled surrogate-RUL assignment

The 100 non-negative Gradient Boosting endpoint predictions are divided into five empirical quintiles using their 20th, 40th, 60th and 80th percentiles. The categories have a sampling function only:

- **Q1:** shortest 0--20% of C-MAPSS endpoint predictions;
- **Q2:** 20--40%;
- **Q3:** 40--60%;
- **Q4:** 60--80%;
- **Q5:** longest 80--100%.

One value is sampled from each quintile, then the five values are permuted across A1--A5. This guarantees that each five-asset scenario spans the available C-MAPSS degradation-state range. Quintiles are used because the simulation contains five virtual assets; they are not warehouse maintenance categories or failure thresholds.

The base assignment uses seed 42. Stability testing uses 1,000 explicitly recorded seeds from 42 to 1,041. As an assignment-design sensitivity check, the same seed sequence is also used for unstratified random samples of five endpoint predictions without replacement. Differences between the stratified and unstratified summaries expose dependence on the quintile-control rule.

## 5. Author-developed priority index

```text
Urgency_i = clip(1 - Surrogate_RUL_Input_i / H, 0, 1)

Consequence_i = w_c * Criticality_i / 5
              + w_t * Throughput_i / 5
              + w_s * Severity_i / 5

Priority_i = 100 * Urgency_i * Consequence_i
```

Base parameters:

- planning horizon `H = 125` abstract cycles;
- equal weights `w_c = w_t = w_s = 1/3`;
- non-negative weights that must sum to one;
- no warehouse probability-of-failure term.

The base horizon is a round author-set value inside the observed prediction range that leaves both active and gated observations. The alternatives 100 and 150 place the boundary 25 abstract cycles below and above the base case. The horizon is therefore a scenario normalisation threshold, not a training-target cap or an empirically established warehouse maintenance interval. Conclusions that change materially across these values must be reported as horizon-dependent.

Equal weights are the base case because no empirical warehouse evidence supports privileging one consequence dimension. The three focal-weight alternatives test different assumed managerial emphases, and every scheme uses non-negative weights that sum to one.

The multiplicative structure requires both near-term urgency and warehouse consequence for a high score. Urgency acts as a gate: a surrogate input at or beyond `H` receives zero priority in the current planning window. This is a transparent author-developed decision rule, not a standard FMEA/FMECA equation.

## 6. Baselines and sensitivity analysis

### 6.1 Simple baselines

- **RUL-only baseline:** `100 * Urgency`; tests whether scenario context changes the order produced by the surrogate input alone.
- **Criticality-only baseline:** `20 * Criticality`; tests whether the composite index adds information beyond the simplest warehouse importance ranking.

### 6.2 Parameter sensitivity

Planning horizons:

- 100 cycles;
- 125 cycles;
- 150 cycles.

Weight schemes:

| Scheme | Criticality | Throughput | Severity |
|---|---:|---:|---:|
| Equal | 1/3 | 1/3 | 1/3 |
| Criticality-heavy | 0.50 | 0.25 | 0.25 |
| Throughput-heavy | 0.25 | 0.50 | 0.25 |
| Severity-heavy | 0.25 | 0.25 | 0.50 |

All schemes sum to one. Ablation removes one consequence component at a time and redistributes equal weight across the two retained components.

### 6.3 Repeated robustness tests

- quintile-stratified surrogate-input assignment: 1,000 recorded seeds;
- unstratified assignment-design sensitivity: the same 1,000 seeds;
- adjacent-anchor score sensitivity: every feasible one-step score change in every stratified assignment;
- prediction-noise simulation: 1,000 recorded seeds around the fixed base assignment;
- noise source: centred out-of-fold C-MAPSS prediction errors from the selected Gradient Boosting model;
- negative perturbed surrogate inputs: clipped to zero.

Reported measures include mean rank, rank standard deviation, probability of rank one, Spearman correlation, Kendall correlation, exact-order agreement and top-ranked-asset agreement.

## 7. Interpretation criteria

The revised evidence can support only the following claims:

- the RUL model has stated predictive performance on C-MAPSS FD001;
- the author-developed priority index satisfies predeclared mathematical checks;
- rankings show a measured degree of stability or sensitivity under controlled changes;
- warehouse scenario variables can change the ranking relative to simple baselines.

The evidence cannot establish warehouse-asset RUL accuracy, observed warehouse risk, real-world ranking validity, realised throughput improvement, cost savings, an optimal maintenance schedule or operational effectiveness.
