# Sententia corpus

Fixed reference corpus for the RAG retrieval layer (phase 2 onward). All documents are genuine primary-source text, manually sourced from [AustLII](https://www.austlii.edu.au/) — no scraper, no fabricated or paraphrased-as-quoted text. Each file is trimmed to the genuinely relevant excerpt(s), not always the full document, but the retained text is verbatim.

Covers NSW residential tenancy law across four topics: termination for renovations/demolition, repairs, rent increases, and bond disputes. No Commonwealth statute is included — residential tenancy law in Australia is state-regulated, and no Commonwealth Act was found to genuinely bear on these topics.

## Legislation (`legislation/`)

| File | Sections | Topic |
|---|---|---|
| `rta2010_s41_rent_increases.txt` | s 41 | rent increases |
| `rta2010_s44_excessive_rent.txt` | s 44 | rent increases |
| `rta2010_s63_65_repairs.txt` | ss 63, 64, 65 | repairs |
| `rta2010_s87f_87g_termination_renovation_demolition.txt` | ss 87F, 87G | termination for renovations/demolition |
| `rta2010_s100_tenant_early_termination.txt` | s 100 | termination (tenant-initiated — **deliberate distractor**, see note below) |
| `rta2010_s159_163_168_bonds.txt` | ss 159, 163, 168 | bond disputes |

All from the *Residential Tenancies Act 2010 (NSW)*, as consolidated on AustLII (current as at 28 October 2025).

**Note on s 100:** the project's stub `search` node (phase 1) used a fake citation of "s 100" for the running example query ("can a landlord end a lease early for renovations"). Section 100 actually governs *tenant*-initiated early termination (social housing offer, aged care, asbestos register, landlord's proposed sale) — it has nothing to do with a landlord terminating for renovations, which is s 87F. Rather than silently fix the stub's placeholder citation, s 100 is kept in the corpus as a deliberate near-miss/distractor: real retrieval (phase 2) has to correctly prefer s 87F over this superficially-similar-sounding but wrong section.

## Cases (`cases/`)

| File | Citation | Topic |
|---|---|---|
| `al-basry_v_maharaj_2022_nswcatcd_9.txt` | [2022] NSWCATCD 9 | repairs / fit for habitation |
| `stewart_v_wang_2024_nswcatcd_70.txt` | [2024] NSWCATCD 70 | renovations (disruption to tenant, not landlord termination) |
| `dawson_v_gj_investments_2024_nswcatcd_40.txt` | [2024] NSWCATCD 40 | repairs + retaliatory termination (s 115) |
| `atkinson_v_papadakis_2025_nswcatcd_154.txt` | [2025] NSWCATCD 154 | rent increases (excessive rent, s 44) |
| `dib_v_holstein_2025_nswcatcd_19.txt` | [2025] NSWCATCD 19 | bond disputes |
| `elsom_v_coroneos_2016_nswcatcd_47.txt` | [2016] NSWCATCD 47 | renovations (uninhabitable test, s 43) |

All from the NSW Civil and Administrative Tribunal, Consumer and Commercial Division (NSWCATCD).

**Gap, noted honestly:** no case in this corpus squarely litigates a landlord terminating a tenancy under s 87F on the merits (i.e. disputing whether the renovation ground was "genuine"). Targeted AustLII searches for this turned up nothing litigated at NCAT — plausibly because the s 87F ground is largely procedural (notice period + timing) with little room for a tenant to contest it, so it rarely reaches a written decision. The two "renovation" cases included instead concern tenant-side disruption claims (noise/dust from a *neighbouring* renovation) rather than the landlord invoking s 87F directly.

Target was 8-10 cases per the original brief; landed at 6 after prioritising genuine, verified, on-topic decisions over padding with weak matches.
