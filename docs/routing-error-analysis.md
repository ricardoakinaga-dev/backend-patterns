# Backend Patterns Phase 1.2 — Routing Error Analysis

This audit is generated from `docs/routing-results.json` after the Phase 1.2 router integration. The router consumes only the public task projection; the taxonomy is evaluator-only. The frozen binary baseline is the pre-edit matcher and contains exactly 148 omitted pairs.

## Release metrics

| Metric | Baseline | Phase 1.2 | Target |
|---|---:|---:|---:|
| Reference precision | 0.9174 | 1.0000 | ≥ 0.90 |
| PRIMARY recall | 0.7280 | 1.0000 | ≥ 0.85 |
| PRIMARY+SECONDARY recall | 0.5171 | 1.0000 | ≥ 0.75 |
| Average selected context | 50,764.62 B | 82,029.69 B | report, no load-all fallback |
| P95 selected context | 80,691 B | 121,998 B | report |
| Baseline omitted pairs | 148 | preserved | 148 enumerated |
| Current labeled omissions | — | 1 OPTIONAL | no PRIMARY/SECONDARY omission |

`reference_precision` and the PRIMARY/SECONDARY metrics are computed against the evaluator-only taxonomy. `binary_reference_recall` remains available for comparison with the Phase 1.1 recommended-reference baseline. OPTIONAL depth references are not release-blocking.

## Disposition policy

- `router_defect`: a PRIMARY omission with no public trigger; none remain in the integrated route.
- `depth_gap`: a SECONDARY omission; none remain in the integrated route.
- `accepted_omission`: an OPTIONAL reference intentionally left out of the bounded route.
- The 148 baseline records below remain immutable evidence of the pre-edit recall gap; they are not relabeled away.

## Frozen baseline omission inventory

All 148 pairs are enumerated below as `scenario :: reference :: level :: disposition`.

001. `G-08 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
002. `SU-002 :: api-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
003. `SU-002 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
004. `G-06 :: api-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
005. `G-06 :: consistency-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
006. `G-06 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
007. `SU-004 :: api-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
008. `SU-004 :: consistency-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
009. `SU-004 :: data-access-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
010. `SU-004 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
011. `SU-005 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
012. `G-02 :: api-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
013. `G-02 :: messaging-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
014. `G-02 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
015. `G-04 :: messaging-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
016. `G-04 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
017. `G-04 :: resilience-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
018. `SU-008 :: api-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
019. `SU-008 :: consistency-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
020. `SU-008 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
021. `SU-008 :: transaction-patterns.md :: OPTIONAL :: accepted_omission` — legacy-optional-omission
022. `SU-010 :: concurrency-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
023. `SU-010 :: idempotency.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
024. `SU-010 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
025. `G-10 :: consistency-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
026. `G-10 :: data-access-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
027. `G-10 :: transaction-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
028. `G-19 :: consistency-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
029. `G-19 :: messaging-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
030. `G-19 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
031. `G-01 :: domain-modeling.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
032. `G-03 :: api-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
033. `G-03 :: data-access-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
034. `G-03 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
035. `G-03 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
036. `G-05 :: anti-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
037. `G-05 :: api-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
038. `G-05 :: consistency-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
039. `G-05 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
040. `G-18 :: consistency-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
041. `G-18 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
042. `G-18 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
043. `G-07 :: anti-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
044. `G-09 :: data-access-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
045. `G-09 :: transaction-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
046. `SR-007 :: anti-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
047. `SR-007 :: consistency-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
048. `SR-007 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
049. `SR-008 :: anti-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
050. `SR-008 :: architecture-boundaries.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
051. `SR-009 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
052. `SR-009 :: security-boundaries.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
053. `SR-010 :: anti-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
054. `SR-010 :: architecture-boundaries.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
055. `SR-011 :: anti-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
056. `SR-011 :: consistency-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
057. `SR-011 :: resilience-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
058. `SR-011 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
059. `SR-012 :: anti-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
060. `SR-012 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
061. `SU-101 :: api-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
062. `SU-101 :: concurrency-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
063. `SU-101 :: transaction-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
064. `SU-103 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
065. `SR-101 :: domain-modeling.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
066. `SR-102 :: architecture-boundaries.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
067. `SR-102 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
068. `SR-103 :: anti-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
069. `SR-103 :: data-access-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
070. `SR-103 :: migration-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
071. `SR-103 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
072. `SR-103 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
073. `NE-101 :: domain-modeling.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
074. `NE-102 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
075. `NE-102 :: performance-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
076. `NE-103 :: data-access-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
077. `NE-103 :: migration-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
078. `NE-104 :: data-access-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
079. `NE-104 :: distributed-systems.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
080. `NE-104 :: migration-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
081. `NE-105 :: architecture-boundaries.md :: PRIMARY :: router_defect` — legacy-primary-omission
082. `NE-105 :: data-access-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
083. `NE-105 :: migration-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
084. `NE-106 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
085. `NE-106 :: resilience-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
086. `NE-106 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
087. `NE-107 :: concurrency-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
088. `NE-107 :: data-access-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
089. `NE-108 :: consistency-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
090. `NE-108 :: distributed-systems.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
091. `BF-102 :: data-access-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
092. `BF-103 :: testing-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
093. `BF-105 :: idempotency.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
094. `BF-105 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
095. `BF-106 :: migration-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
096. `BF-107 :: architecture-boundaries.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
097. `BF-107 :: idempotency.md :: PRIMARY :: router_defect` — legacy-primary-omission
098. `BF-107 :: messaging-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
099. `BF-107 :: observability-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
100. `BF-107 :: transaction-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
101. `FD-101 :: messaging-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
102. `FD-101 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
103. `FD-101 :: resilience-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
104. `FD-102 :: resilience-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
105. `FD-102 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
106. `FD-103 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
107. `FD-104 :: observability-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
108. `FD-105 :: concurrency-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
109. `FD-105 :: performance-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
110. `FD-105 :: resilience-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
111. `FD-106 :: consistency-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
112. `FD-106 :: observability-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
113. `FD-107 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
114. `FD-107 :: resilience-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
115. `FD-107 :: transaction-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
116. `SEC-101 :: api-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
117. `SEC-101 :: data-access-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
118. `SEC-102 :: transaction-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
119. `SEC-103 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
120. `SEC-103 :: resilience-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
121. `SEC-104 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
122. `SEC-104 :: resilience-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
123. `SEC-105 :: api-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
124. `SEC-106 :: api-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
125. `SEC-106 :: testing-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
126. `SEC-107 :: observability-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
127. `SEC-107 :: performance-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
128. `SEC-107 :: resilience-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
129. `SEC-108 :: migration-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
130. `OP-101 :: distributed-systems.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
131. `OP-101 :: messaging-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
132. `OP-101 :: transaction-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
133. `OP-102 :: observability-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
134. `OP-102 :: security-boundaries.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
135. `OP-103 :: observability-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
136. `OP-103 :: testing-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
137. `OP-103 :: transaction-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
138. `OP-105 :: api-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
139. `OP-105 :: observability-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
140. `OP-105 :: resilience-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
141. `OP-106 :: idempotency.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
142. `OP-106 :: performance-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
143. `OP-107 :: concurrency-patterns.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
144. `OP-107 :: messaging-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
145. `OP-107 :: observability-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission
146. `OP-107 :: security-boundaries.md :: PRIMARY :: router_defect` — legacy-primary-omission
147. `OP-108 :: distributed-systems.md :: SECONDARY :: depth_gap` — legacy-secondary-omission
148. `OP-108 :: resilience-patterns.md :: PRIMARY :: router_defect` — legacy-primary-omission

## Current omission inventory

- `SU-008 :: transaction-patterns.md :: OPTIONAL :: accepted_omission` — OPTIONAL reference is depth-only progressive disclosure and is intentionally not selected in the bounded route.

## Interpretation

The active route reaches all taxonomy-labeled PRIMARY and SECONDARY references in the 72-case corpus with no taxonomy-irrelevant load. The one remaining omission is the OPTIONAL transaction depth reference for the mixed-version rollout case. Mutation checks separately confirm that legacy terms, effect-safety, atomic-boundary and migration bundles are causally active, and that adding evaluator-only gold fields does not change routing.

The route is still deterministic lexical/compositional evidence, not a claim about consumer-model behavior. Model control/treatment, real composition and backend runtime remain separate host-capability gates.
