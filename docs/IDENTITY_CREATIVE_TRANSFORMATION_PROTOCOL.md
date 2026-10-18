# Strokera ICCT Protocol 0.1
## Identity Consistency × Creative Transformation
**Status:** Proposed research and production protocol (not yet implemented)  
**Version:** 0.1 / 2026-10-18  
**Scope:** Character-IP illustration, editorial artwork, and controlled visual transformations

> **核心原则：保留人物身份，而不是保留原始图片。**
>
> **Preserve the character's identity, not the source image's pose, costume, or scene.**

### 1. Purpose and boundaries

Strokera should support **two deliberately different types of work**. They must never share an implicit, one-size-fits-all fidelity requirement:

| Mode | Intended task | Non-negotiable constraints | Changes permitted |
| --- | --- | --- | --- |
| `SOURCE_FIDELITY` | Photo-to-line-art, garment isolation, printing restoration, faithful product imagery | Approved original, subject/garment geometry and specified details | Only specifically authorized cleanup and style-processing changes |
| `IDENTITY_CREATIVE` | Character-IP storytelling, poses, professions, scenes, clothing redesign, American-style doodle/comic reinterpretation | Stable character identity and specifically locked character traits | Pose, clothing, environment, activity, camera, expression, supporting objects, style, composition—when allowed by the brief |

A commission must explicitly declare its mode. A creative brief cannot silently relax `SOURCE_FIDELITY` constraints; a `SOURCE_FIDELITY` task must not be evaluated as though original pose and clothing could be freely redesigned.

**Relationship to existing standards:** This document defines a proposed character-IP workflow and evaluation methodology. It does **not** alter `spp/0.1`, the existing CLI, or assert that identity scoring, reference conditioning, GPU workflows, or creative generation already exist in the codebase.

### 2. Character identity contract

An IP is a **coherent, recognizable character across changing situations**, not a single unchanged picture.

For each approved character, maintain an **Identity Bible** (identity reference set) where lawful and available:

- `character_id`, IP name, creator/rights holder, reference usage permissions, and revision.
- Immutable, rights-cleared original images or approved character masters, with content hashes; use several authorized views where possible.
- **Protected traits:** facial structure and proportions, characteristic eye/nose/mouth relations, defining hairstyle/hairline, body proportions, and distinctive markings/accessories *only if those are intrinsic to the character*.
- **Flexible traits:** expression, action, camera angle, hairstyle variation, clothing, profession, season, scene, objects, composition, art treatment, and narrative context, unless the owner specifically locks one.
- Owner-approved examples of **same character / different scene** and **identity drift / rejection**, with notes on ambiguity.
- Any known limitations (e.g., no approved side-view; accessories obscure the face); do not infer unobserved identity details as ground truth.

**Identity must not be equated with identical pixels.** Strong transformations can preserve recognition while changing viewpoint and styling. Conversely, copying hair color and clothes is not proof of consistent facial identity.

### 3. Creative brief: what may change

Every `IDENTITY_CREATIVE` job states:

1. **Who:** character ID and approved reference revision.
2. **What to protect:** explicit core identity traits, plus any scene-specific locks.
3. **What to reinvent:** pose, expression, wardrobe, occupation, vehicle, location, props, composition, lighting, style and action.
4. **Narrative objective:** the story/role portrayed, rather than a list of decorative symbols.
5. **Visual direction:** e.g., American doodle, dynamic comics, fashion editorial, color palette, transparent background and printable edges.
6. **Forbidden alterations:** changes that would break character identity, exceed permissions, or misrepresent the source as an unchanged documentary photograph.
7. **Deliverables and review:** image outputs, alpha/background requirement, size/print constraints, review checkpoints and acceptance criteria.

**Example — finance character IP:** A woman known from a white-shirt standing portrait becomes a quant researcher on a fast-moving bicycle, with her recognizable face and character silhouette, a redesigned outfit and pose, and K-lines/market plots integrated into motion and narrative. **Do not** simply paste chart icons behind the original standing pose and call it creative transformation. Financial graphics in fictional art are illustrative; do not fabricate performance evidence or suggest investment returns are guaranteed.

### 4. Transformation workflow (proposed)

```text
Rights-cleared originals / approved character masters (immutable)
          ↓
Character Identity Bible (versioned; protected / flexible traits)
          ↓
Declare mode + approve creative brief
          ↓
Generate independent candidate drafts from approved source references
          ↓
Identity review + creative-transformation review
          ↓
Reject / revise / human-select approved master
          ↓
Controlled processing (alpha, edges, layers, print preflight if needed)
          ↓
Archive source lineage, candidate metadata, assessments and final asset
```

Rules:

- **One source-of-truth, independent drafts.** Reference approved originals/masters for each new candidate; do not default to repeatedly using yesterday's generated output, which compounds identity drift.
- **Intentional evolution is versioned.** If an artist approves a changed character design, publish an explicit new Identity Bible revision, rather than silently overwriting the old one.
- **Separate invention from restoration.** Generated poses, garments and scenes are creative inventions; they are not claims about physical features hidden in the original photograph.
- **Human approval governs identity.** Automated comparisons can flag suspicious drift but are not sufficient to declare a character canonical.
- **Rights and consent first.** Use images that the project has the right to transform; follow identity/likeness permissions, provenance, privacy, and applicable restrictions on misleading real-person imagery.

### 5. Evaluation: two independent axes

**Identity Consistency (IC)**: Does the result still read as the *same* approved character, across changed scenes?  
**Creative Transformation (CT)**: Is the change meaningful, original within the brief, and integrated into the composition rather than merely decorative?

Evaluate both separately. **“IC × CT” describes a dual objective, not an automatically valid arithmetic product or a claim of measured model performance.** A high score on one axis cannot erase failure on the other.

Initial **human-review rubric (proposed, 1–5 ordinal; not yet calibrated)**:

| Score | IC — identity consistency | CT — creative transformation |
| --- | --- | --- |
| 1 | Clearly another character | Minor color/filter changes; almost no new concept |
| 2 | Major drift in defining features | Cosmetic additions around the original subject |
| 3 | Partially recognizable, meaningful discrepancies | Some new action/context, weak narrative integration |
| 4 | Clearly same character, minor acceptable variation | Convincing new pose/scene/role, well-integrated graphic language |
| 5 | Recognizably same IP across a substantial visual change | Original, coherent transformation with strong storytelling and aesthetics |

**Initial acceptance proposal (subject to calibration):** For `IDENTITY_CREATIVE` use IC ≥ 4 **and** CT ≥ 4, plus all mandatory locks and rights checks passing. Reviewers may mark **unsure** and request more source references rather than force a score. For `SOURCE_FIDELITY`, CT is **not** a quality target; evaluate geometric/source-specific fidelity, masks, print requirements and agreed constraints instead.

Recommended supplemental signals (research hypotheses, not implemented claims):
- Face and body landmark geometry under matched viewpoints; assess occlusion and viewpoint confounds.
- Human pairwise same-character judgments (blinded across generators when possible).
- Diversity of approved poses, clothing and scene semantics relative to the creative brief.
- Artifact checks: extra limbs/fingers, broken garments, texture hallucination, empty/opaque background when transparency required.
- Subject extraction/alpha matting quality, edge halos, resolution and print suitability.
- Revision rate, review minutes, rejection reasons, and cost per approved asset.

**Do not set a universal face-embedding threshold as identity truth.** Computer-vision similarity is susceptible to viewpoint, age/styling changes, and dataset bias. Document disagreement between numeric checks and humans; use representative approved references and explicit reviewer sign-off.

### 6. Suggested production record (design sketch, not an existing API)

```yaml
protocol: strokera/icct-0.1
job_id: ip-creative-0001
mode: IDENTITY_CREATIVE
character_id: character-example
identity_bible_revision: "1"
source_refs:
  - asset_id: authorized-master-01
    sha256: "<source-file-sha256>"
rights_review: approved
creative_brief:
  narrative: "Quant researcher in a dynamic market-themed scene"
  protected: ["facial identity", "character-defining proportions"]
  allowed: ["pose", "outfit", "setting", "props", "composition"]
  style: "American doodle / comic editorial"
  transparent_background: true
generation:
  tool: "<tool-or-model>"
  version: "<model-version-if-available>"
  parameters_ref: "<recorded-parameters-or-prompt-hash>"
  candidate_id: "<immutable-candidate-id>"
review:
  identity_score: null
  creativity_score: null
  constraints_passed: null
  reviewer: null
  decision: pending
outputs:
  approved_master: null
  alpha_qc_report: null
  production_report: null
```

The schema above illustrates **what to record**; it is not parsed by current Strokera software. Hashes, reference IDs, versions, prompts when releasable, review criteria and every approval decision belong in traceable records.

### 7. Research protocol and baseline experiment

Begin with a **small, permissions-cleared** evaluation set, not a giant uncategorized image dump:

1. Approve one or more characters with several independent identity references and written protected traits.
2. Define four briefs per character: restrained pose variation, wardrobe/professional role change, dynamic action, and dramatic composition/style shift.
3. Generate independent candidates from the same approved references; log model versions, instructions, seeds where supported and costs.
4. Compare **identity-only copy / decorative-addition baseline** against a **deliberate story-driven transformation** without conflating them.
5. Obtain independent human judgments for IC/CT and concrete failure labels; review borderline cases with the IP owner.
6. Test MATLAB/Python analysis methods only as supporting evidence; examine reviewer agreement and error types before claiming quantitative validity.
7. Promote a method to repeatable production only after defined evaluation, lineage capture and regression cases. Preserve rejected samples as labeled research data when permitted.

Publish results as **experiment reports**, not marketing claims. A high CT score cannot compensate for failure to preserve an IP; a high IC score with no reinvention cannot satisfy an ambitious creative brief.

### 8. Development and acceptance

Keep Codex/AI changes in **small, reviewable 15–30 minute microtasks**, with one measurable objective per change. Suggested initial tasks (not automatically scheduled):

- **ICCT-001:** Define an Identity Bible JSON/YAML schema and sample; validate required fields and rights status.
- **ICCT-002:** Add explicit `mode` and locked/flexible traits to a separate proposed production-manifest schema (do not break SPP 0.1).
- **ICCT-003:** Build a human-review form that stores separate IC and CT scores with rejection reasons.
- **ICCT-004:** Build a small baseline comparison report from consented samples and reviewer ratings.
- **ICCT-005:** Add transparent-background and subject-edge QC to approved masters.

A microtask is done only when its changed files, input/output contracts, tests or document examples, reproducibility notes, and acceptance evidence are provided. Do not implement batch GPU generation and experimental scoring in a single large unsupervised task.

### 9. Canonical principle / 规范声明

**中文：** Strokera 的原图保真与人物 IP 二创是两条不同的生产路径。原图保真保护原始几何和细节；人物二创保护身份与人格识别，同时允许对姿势、服装、职业、场景和叙事进行充分创造。最终目标不是“每次画得一样”，而是“在不同的作品里，仍然是同一个人物”。

**English:** Source fidelity preserves the authorized original. Character-IP creation preserves the recognizable character while transforming the world around—and sometimes the pose and presentation of—that character. Strokera must measure **continuity of identity and quality of invention independently**, then make approvals traceable.
