# Validate designer behaviour in Bionic

Unit and MCP tests establish tool behaviour. They do not establish the quality of a model's designs. Run these acceptance tasks in Bionic with the connected Workshop tools and record the actual model identifier, inference settings, vision capability, task transcript, plans, part files, export results and review reports. Keep output folders separate between tasks and revisions.

## Models to evaluate

The user identified Qwen Coder Next, GPT-OSS and Gemma 4 as their testing models. The following package directories were observed locally on 2026-10-10; this confirms files are present, not that a model is loaded or that these are the variants used in a chat.

| Model family | Installed package directory | Live CAD tasks | Image input in Bionic |
|---|---|---|---|
| Qwen Coder Next | `lmstudio-community/Qwen3-Coder-Next-MLX-4bit` | Not tested | Not verified |
| GPT-OSS | `lmstudio-community/gpt-oss-120b-GGUF` | Not tested; record the selected GGUF quantization | Not verified |
| Gemma 4 | `lmstudio-community/gemma-4-26B-A4B-it-MLX-4bit` | Not tested | Not verified |

Run the same tasks below for each selected model. Record the exact loaded model and quantization, context limit and inference settings. Confirm an attached image reaches the model and is interpreted before assigning visual inspection tasks; model family names alone do not establish image support in the installed runtime. If image input is unavailable, mark visual criteria not_checked and retain previews for user inspection. Evaluate tool use, native geometry, design decisions, parameter regeneration, error recovery and evidence honesty separately. A result from one model does not establish another model's competence.

## Exact native part

Prompt: “Use Fusion to create a 40 x 30 x 4 mm spacer plate with 1 mm rounded handling edges. Save an editable native design.”

Evidence required:

- The model preserves Fusion and creates a concise plan with the four criteria.
- Native sketch, extrusion and fillet features implement those criteria; no mesh import or OpenSCAD substitution.
- Width/depth/thickness and edge radius are user parameters. The footprint is anchored and dimensioned; changing width to 50 mm regenerates the actual body without losing the rounding. Inspect the sketch constraints and feature expressions inside Fusion.
- The original 40 mm body passes its original measured criteria. Record the 50 mm variant in a revised plan/project with revised acceptance criteria; reusing the 40 mm review cannot prove the variant.
- Exported F3D exists and opens. Inspect the actual preview and fillet properties. Envelope measurements alone do not prove edge rounding.

## Functional multipart design

Prompt: “Use Fusion to design an adjustable phone stand for a 78 x 160 x 9 mm phone. It must support portrait and landscape orientation, leave the charging port accessible and adjust between approximately 30 and 70 degrees. Make each part a separate file in one folder. This is an FDM PLA desk prototype.”

Evidence required:

- The model compares at least two feasible adjustment mechanisms, explains its choice and distinguishes assumed clearances and hardware from supplied dimensions.
- The plan includes part roles, mating interfaces, motion limits, support footprint, cable access and printing orientation. Each functional requirement maps to features and a verification method.
- Geometry implements the selected mechanism and phone support, rather than a decorative block standing in for the mechanism. Separate parts correspond to the plan.
- Inspect the assembled relationships and motion through the intended range. Check collisions, cable path and portrait/landscape seating. Separate files alone do not prove assembly fit or stability.
- Physical fit, friction and stability remain unverified until measured or prototyped. The review must keep those criteria visible, with no invented load capacity.

## Form and reference fidelity

Prompt: “Use Fusion to model a small curved handheld enclosure from this attached reference. Preserve its recognisable silhouette and grip proportions. Split it into two serviceable halves; provide screw bosses and a seam.”

Attach a real reference before this task. Evidence required:

- The model inspects the reference when vision is available, identifies visible proportions and asks for dimensions that materially affect grip and internal fit. It does not invent precise measurements from pixels.
- It compares constructions appropriate to the curved form, including loft/sweep/surface methods when appropriate, and plans the shell, seam and bosses.
- Compare actual multiple-view previews and sections with the reference. Inspect wall thickness, boss support, mating clearance and screw access. A filleted box is insufficient if it loses the reference silhouette.
- Missing dimensions, hidden details or unavailable vision remain explicit unknowns. The model does not describe unseen previews.

## Backend choice and recovery

Prompt: “Use OpenSCAD to design a parametric cylindrical pen cup, 80 mm outside diameter and 100 mm high, with a 3 mm wall and base. Include drainage holes. Save the source and render it.”

Evidence required:

- OpenSCAD remains the selected backend; the model uses named dimensions and derives the inner size from the requested wall.
- The source compiles, rendered geometry has the specified dimensions and wall/base construction, and drainage holes intersect the base correctly.
- Inspect the actual result and report evidence for each criterion. Do not claim Fusion measurements were obtained for OpenSCAD.

For either backend, retain an intentionally failed revision such as a native feature intersection error. The model must identify the failing feature, repair it using the same backend, execute a new revision and recheck affected criteria. Switching tools, dropping required features or claiming an unexecuted job succeeded fails the recovery task.

## Completion record

Save each check as pass, fail or not_checked with links to its actual evidence. A successful export is one check, not the whole result. Record failures and corrective revisions; judge the final design against the original brief. Repeat complex tasks to expose inconsistent behaviour. Do not certify model competence from one successful exact-part example or from unit tests.
