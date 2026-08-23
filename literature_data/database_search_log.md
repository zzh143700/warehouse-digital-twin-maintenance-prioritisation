# Dissertation-wide database search log / 全论文数据库检索记录

## Scope / 范围

Search date: **16 August 2026**  
Research question: **Can AI-predicted Remaining Useful Life generate risk-based maintenance priority rankings in a conceptual warehouse digital twin?**

This search updates and triangulates the existing 64-full-text evidence set. It does not retrospectively replace the original PRISMA counts. The update was conducted through the University of Warwick Library's authenticated access to **Web of Science Core Collection**, **Scopus**, and **EBSCOhost Business Source Ultimate**. Crossref was then used only to verify bibliographic metadata and DOI records for shortlisted items.

本次检索用于更新并交叉核验原有的 64 篇全文证据集，而不是倒推修改既有 PRISMA 数字。检索通过 Warwick Library 的机构访问完成，覆盖 Web of Science Core Collection、Scopus 和 EBSCOhost Business Source Ultimate；Crossref 仅用于核对入选文献的作者、年份、期刊及 DOI。

## Search controls / 检索控制

- Web of Science searches used the **Topic** field. Results were normally sorted by **Citations: highest first**.
- Scopus searches used **Article title, Abstract, Keywords**. Results were sorted by **Cited by (highest)**.
- EBSCOhost was limited to **Business Source Ultimate** and **peer-reviewed journals**. Results were screened in relevance order.
- Older sources were retained only where they are field-defining or methodologically necessary. Recent sources were preferred for current Digital Twin, RUL and warehouse applications.
- Search-result counts are platform-specific displayed counts. They should not be added together because database coverage overlaps substantially.

## Comparable query clusters and displayed results / 可比检索主题与显示结果数

| ID | Search cluster and Boolean query | Web of Science | Scopus | EBSCO BSU, peer reviewed |
| --- | --- | ---: | ---: | ---: |
| Q1 | `"remaining useful life" AND ("predictive maintenance" OR "condition-based maintenance") AND (decision* OR priorit* OR schedul*)` | 587 | 923 | 55 |
| Q2 | `"digital twin*" AND ("predictive maintenance" OR prognostic* OR "remaining useful life")` | 1,758 | 3,180 | 104 |
| Q3 | `("risk-based maintenance" OR "condition-based maintenance") AND (priorit* OR rank* OR criticality OR consequence OR "multi-criteria")` | 440 | 852 | 77 |
| Q4 | `("automated warehouse" OR "warehouse automation" OR intralogistics) AND (maintenance OR reliability OR availability OR downtime OR "digital twin")` | 141 | 292 | 30 |
| Q5 | `"digital twin*" AND (dashboard* OR visuali?ation OR "visual analytics" OR "decision support") AND (maintenance OR manufacturing OR warehouse*)` | 849 | 1,474 | 115 |

Two additional Web of Science checks were recorded:

- Broad warehouse context: `(warehouse* OR intralogistics OR "material handling") AND (maintenance OR reliability OR downtime OR criticality OR "digital twin*")` — **2,196** results. This query was too broad for direct inclusion because many records concerned unrelated sensing, construction and supply-chain topics.
- Warehouse Digital Twin focus: `(warehouse* OR intralogistics OR "material handling") AND "digital twin*"` — **266** results. This was useful for identifying logistics simulation, internal transport and automated-warehouse studies.

## Cross-database convergence / 多数据库交叉结果

The two citation databases converged strongly on several established sources. Examples include the RUL review by Zhang et al. (2018), the Digital Twin–PHM paper by Tao et al. (2018), the CNC Digital Twin case by Luo et al. (2020), and the predictive-maintenance overview by Achouch et al. (2022). This convergence supports their use as anchors rather than relying mainly on very recent single studies.

Web of Science and Scopus also returned the same warehouse-adjacent evidence: logistics simulation and Digital Twins (Agalianos et al., 2020), internal transport systems (Kosacka-Olejnik et al., 2021), an AMR case study (Stączek et al., 2021), automated high-rise warehouse optimisation (Leng et al., 2019), and in-house logistics decision support (Coelho, Relvas and Barbosa-Póvoa, 2021).

EBSCO Business Source Ultimate added a management and decision-support perspective. Its results included maintenance-decision optimisation, warehouse automation, visual analytics and operational decision support. EBSCO results were treated as complementary evidence rather than as a substitute for the engineering coverage of Web of Science and Scopus.

## Screening outcome / 筛选结果

### Include in the dissertation-wide evidence library

Eighteen verified additions were selected because they fill a specific chapter-level gap and have a DOI:

1. Achouch et al. (2022) — current predictive-maintenance overview and challenges.
2. Agalianos et al. (2020) — logistics simulation and Digital Twin review.
3. Azizi and Fathi (2014) — fuzzy AHP maintenance-strategy selection; retained as a method comparator.
4. Bevilacqua and Braglia (2000) — field-defining AHP maintenance-strategy study.
5. Coelho, Relvas and Barbosa-Póvoa (2021) — empirical/simulation-based in-house logistics decision support.
6. Kosacka-Olejnik et al. (2021) — internal transport Digital Twin review.
7. Kunath and Winkler (2018) — integration of a manufacturing Digital Twin into a decision-support system.
8. Leng et al. (2019) — automated warehouse Digital Twin optimisation.
9. Luo et al. (2020) — empirical hybrid Digital Twin predictive-maintenance case.
10. Mourtzis and Vlachou (2018) — scheduling combined with condition-based maintenance.
11. Nantee and Sureeyatanapas (2021) — Logistics 4.0 and automated-warehouse performance.
12. Prajapati, Bechtel and Ganesan (2012) — condition-based-maintenance survey.
13. Stączek et al. (2021) — empirical AMR Digital Twin case.
14. Tao et al. (2018) — Digital Twin-driven prognostics and health management.
15. Wright and Davidson (2020) — boundary between a model and a Digital Twin.
16. Zhang et al. (2018) — high-impact RUL review using Wiener-process methods.
17. Zheng et al. (2023) — visual analytics framework and case study for Digital Twins.
18. Zhu, Liu and Xu (2019) — manufacturing Digital Twin visualisation using augmented reality.

### Retain as optional comparators

- Very recent 2025–2026 studies already present in Chapter 2 remain useful as examples of current applications, but they should not carry the main theoretical argument where an established review or empirical study is available.
- Conference papers are retained only where they provide a direct method or warehouse-transfer example that is not adequately covered by a journal article.

### Exclude from direct use

- Broad query results without a clear RUL-to-maintenance-decision link.
- Digital Twin papers concerned only with visual replication, city/building twins or unrelated sensing.
- Warehouse papers focused on picking performance or supply-chain strategy without maintenance, reliability or Digital Twin relevance.
- Blogs, news items, Wikipedia and records without verifiable scholarly metadata.

## Interpretation for the dissertation / 对论文的含义

The search supports a dissertation-wide reallocation rather than indiscriminate citation growth. The main bodies of theory should sit in Chapter 2 and Chapter 6. Chapter 3 needs only sources that justify methodological choices. Chapter 4 should remain predominantly results-only. Chapter 5 should analyse the study's own outputs with a small number of comparison sources. Chapter 7 should not introduce new literature.

The resulting master library contains **87 distinct DOI-identified sources plus the IEC standard (88 total)**. This remains within the requested 70–150 range while avoiding an inflated list of weakly used citations.
