# Workshop with Autodesk Fusion: complete guide

Workshop prepares a design job in LM Studio or Bionic. **WorkshopBridge** can run it automatically inside Autodesk Fusion, or you can run **WorkshopDesign** manually. Both export a genuine local `.f3d` archive.

This guide covers the Workshop bridge, not every feature of Autodesk Fusion. The recipe supports boxes, cylinders and new/join/cut operations. Native STEP/STP, IGES/IGS, SAT and F3D import jobs use Fusion’s import manager. Live F3D export is implemented but remains unverified.

## 1. Install or update Workshop

If this is your first installation, download `install.sh`, close LM Studio and run:

```sh
bash install.sh
```

If Workshop is already installed, download the latest `installupdate.sh`, close LM Studio, Bionic and Fusion, then run:

```sh
bash installupdate.sh
```

On macOS you can open Terminal, type `bash ` with the trailing space, drag the downloaded script from Finder into Terminal and press Return. Confirm the prompt and wait for **Installation complete**.

The installer handles Workshop's Python/Node dependencies. Install and open Autodesk Fusion separately. You do not need to compile the Fusion script or install Python inside Fusion.

Restart LM Studio and enable **Workshop: Openscad And Fusion**, or the integration whose identifier is `workshop-openscad-and-fusion`. In Bionic, add the installed `Bionic/SKILL.md` through **Settings → Skills → Add file**, using the path printed by setup.

## 2. Find the Fusion script folder

### Current installation on macOS

1. Open Finder.
2. Press **⌘ Shift G** to open **Go to Folder**.
3. Paste this path and press Return:

```text
~/Library/Application Support/Workshop/fusion/WorkshopDesign
```

The folder should contain:

```text
WorkshopDesign/
├── WorkshopDesign.py
└── WorkshopDesign.manifest
```

Select this **folder** when adding the script to Fusion. The `.py` file contains the code; the `.manifest` file identifies it to Fusion.

### Older installation

If the stable folder above does not exist, either run the updater or use Finder's **⌘ Shift G** with:

```text
~/Library/Application Support/Workshop/releases
```

Open the release folder from your successful installation, then **fusion → WorkshopDesign**. Failed installations may also leave a release directory, so do not choose a folder solely because its date is newest.

After updating, switch the Fusion registration to the stable path in the previous section. Old managed release folders are removed by the updater.

### Extracted source ZIP

If you extracted `workshop.zip`, the script is at:

```text
workshop/fusion/WorkshopDesign
```

Keep that source folder in a permanent location if you register this copy. Moving or deleting it breaks Fusion's reference.

### Custom installation

If you used `WORKSHOP_HOME`, use `<your installation folder>/fusion/WorkshopDesign`. The installer and updater print the full script-folder path when they finish. The Linux shell installer can prepare recipes and source files; the Fusion bridge still requires an environment where Autodesk Fusion itself runs.

## Automatic execution: register WorkshopBridge once

The installer/updater now provides a second folder:

```text
~/Library/Application Support/Workshop/fusion/WorkshopBridge
```

From a source checkout use `fusion/WorkshopBridge`. On Windows or a custom installation, use the corresponding absolute folder path.

Open Fusion’s **Scripts and Add-Ins** window, select **Add-Ins**, add the **WorkshopBridge folder**, then run it and enable **Run on Startup**. Keep the adjacent WorkshopDesign folder; the add-in loads its geometry engine. This registration is required once. The tool cannot bypass Fusion’s add-in registration controls.

After registration, ask the model to prepare a job, call `run_fusion_design` and check `fusion_design_status`. The run tool can launch Fusion on macOS. On Windows set `WORKSHOP_FUSION_APP` to the executable path. Linux can prepare jobs but does not have a supported native Fusion launcher.

The add-in checks a local queue and dispatches work through Fusion custom events on its main thread. It waits until the Select command is active, so finish any active sketch/command if a job stays queued. Pending and queued jobs have not exported. Successful status includes `design_url`, `design_link`, output path, bytes and warnings. Show that link to the user. It is a local archive link, not an Autodesk cloud share URL. `open_fusion_design` queues reopening a saved workspace F3D through the add-in.

Default queue: `~/.workshop/fusion-bridge`. To override it, set `WORKSHOP_FUSION_BRIDGE` in the MCP environment and use the same directory in the add-in’s `bridge-config.json` (`{"directory": "/absolute/path"}`). The installer writes this configuration at the stable add-in path. Do not expose the queue to untrusted users; it runs CAD operations with your local privileges.

Receipts prevent duplicate execution after retries or Fusion restarts. If a run was interrupted, status becomes `execution_unconfirmed`; inspect Fusion and the target file, then prepare a new job/output filename. Opening an archive returns `queued_open`, which is a request, not confirmation that Fusion opened it.

For existing complex CAD, use `prepare_fusion_import(recipe_file="import-job.json", source="part.step", output="part.f3d")`, then run/check the job. Source files must already be in the configured workspace. Meshes and F3Z assemblies are not supported by the native import tool. Advanced geometry uses `prepare_fusion_script`: generate native Python defining `build(design, root)`, then queue it with the same run/status tools. Trusted code must be enabled; the standard installer enables it. Fusion requests stay in Fusion and do not require OpenSCAD or mesh import.

The remaining sections describe the manual script fallback.

## 3. Open Scripts and Add-Ins

1. Open Autodesk Fusion and a design in the **Design** workspace.
2. Find **UTILITIES** in the toolbar tabs above the modelling area.
3. Select **Utilities → Add-Ins → Scripts and Add-Ins**.

You can also try **Shift + S** while Fusion is focused.

If you see a window with a list of scripts, a search box and a **+** at the top, you are already in the correct window. You do not need to find Utilities again.

Autodesk documents the menu route and script controls in [Manage scripts and add-ins](https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-MANAGE-SCRIPTS-ADD-INS.htm).

## 4. Add WorkshopDesign once

In the **Scripts and Add-Ins** window:

1. Find the **+** above the list.
2. In the list-style interface with a small **▼ beside +**, open that dropdown and choose the option to add an existing/local script from your computer. The exact wording varies by Fusion version.
3. Select the **WorkshopDesign folder**, containing both files listed earlier.
4. Confirm the selection.
5. Search for **WorkshopDesign**, or locate it in the list.

In versions with separate **Scripts** and **Add-Ins** tabs, use **Scripts** and its **+** control. WorkshopDesign is a script you run for each job; it does not need to run at startup.

Once it appears, registration is complete. Wait until you have generated a job before running it.

## 5. Ask Workshop to prepare your first design

Use this prompt in LM Studio or Bionic:

> Use Workshop's OpenSCAD and Fusion workflow. Check capabilities and load the workflow. Prepare a Fusion job for a plate 40 mm wide, 30 mm deep and 4 mm thick. Add a 5 mm diameter through-hole with its centre 10 mm from the left edge and 10 mm from the front edge. Use millimetres. Save the job as plate-job.json and request plate.f3d in my workspace. Use prepare_fusion_design and show me the full job path and requested output path. Tell me when the job is ready to run in Fusion.

The model should call `prepare_fusion_design`. A successful preparation returns:

- `recipe_path`: the JSON file to select in Fusion.
- `requested_output`: the eventual F3D file location.
- `status`: `pending_fusion_execution`.

**Pending means the JSON exists; the F3D has not been exported yet.** Call `run_fusion_design` to execute through the registered add-in, or use the manual steps below.

By default, files are prepared under **Documents → Workshop**:

```text
~/Documents/Workshop/plate-job.json
~/Documents/Workshop/plate.f3d
```

If you chose a custom workspace, use the paths returned by the tool. Tool inputs use workspace-relative filenames; the generated job stores the resolved absolute F3D output path.

## 6. Run the job in Fusion

1. Return to **Scripts and Add-Ins** in Fusion.
2. Select **WorkshopDesign**.
3. Click **Run**, or the **▶** in its row in the list-style interface.
4. When **Select Workshop recipe** opens, choose the generated **`plate-job.json`**.
5. Wait for the script to finish.

Choose the job JSON returned by the tool. Do not select `WorkshopDesign.py`, its `.manifest`, an existing `.f3d`, or `examples/plate.json` directly. The example recipe lacks the output path added by job preparation.

The script creates a **new parametric design**. It adds sketches and extrusions for the recipe parts, then exports the F3D archive. It does not modify your existing design as a recipe-edit operation.

On success it displays **Exported genuine Fusion archive** followed by the output path. It also writes a companion result file beside the job:

```text
plate-job.result.json
```

That result contains `status: exported`, the F3D path and the file size. Errors are recorded as `status: error` with diagnostics and a traceback in the result JSON; manual runs also show a Fusion message box. An error is not an export confirmation. Failed geometry remains in the new document for inspection.

## 7. Find and inspect the exported file

For default output paths on macOS:

1. Open Finder and press **⌘ Shift G**.
2. Enter `~/Documents/Workshop`.
3. Find `plate.f3d` and `plate-job.result.json`.
4. Open the F3D in Fusion using its local-file open workflow.
5. Inspect the geometry, dimensions, hole placement and feature timeline.

The script names sketches **Workshop profile 1**, **Workshop profile 2**, and so on. Extrusions are named **Workshop box 1**, **Workshop cylinder 2**, and so on.

A parametric design with sketch/extrude history is created, but the bridge does not create named user parameters or fully dimension/constrain every sketch. Do not treat it as a complete production CAD parameter system.

Autodesk's [Fusion archive export API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ExportManager_createFusionArchiveExportOptions.htm) is used to export the design. Recipe preparation and archive export are separate operations.

## 8. Change the design

To generate a revision, ask Workshop to prepare **new filenames**, for example `plate-v2-job.json` and `plate-v2.f3d`. Then run WorkshopDesign again and select the new job.

The preparation tools and Fusion script refuse to overwrite existing outputs. Each run builds a fresh design. Editing an existing Fusion model, locating its features or updating it in place is not implemented by this bridge. You can make manual edits inside Fusion.

## Supported recipe features

| Feature | Behavior |
| --- | --- |
| Units | Millimetres; the bridge converts values to Fusion API centimetres |
| Part count | 1–100 primitives per job |
| Box | Width, depth and height; origin is its lower corner |
| Cylinder | Diameter and height; origin is the centre of its base |
| Position | `origin: [x, y, z]`; finite numeric coordinates |
| New | Creates a new body; required for the first part |
| Join | Adds material to intersecting existing bodies |
| Cut | Removes material from intersecting existing bodies |
| Extrusion direction | Positive Z from the part's sketch plane |
| Sketch planes | XY plane, with a Z offset when required |
| History | New parametric document with named sketch/extrude features |
| Output | Genuine `.f3d` through Fusion; new filenames required |
| Completion | Export message and companion `.result.json` |

Dimensions must be finite positive numbers. Negative origins are allowed. For a through-hole, make the cutting cylinder extend beyond both surfaces; the sample plate uses a cylinder starting at Z = −1 with height 6 for a 4 mm plate. A cut that misses the body or a join that does not intersect can fail inside Fusion.

The bridge does not currently support recipe primitives for fillets, chamfers, threads, lofts, sweeps, arbitrary profiles, rotations, assemblies, joints, external references or direct mesh export. Advanced geometry uses native Fusion scripts prepared with `prepare_fusion_script` and executed by WorkshopBridge. STEP/IGES/SAT/F3D imports are available separately through `prepare_fusion_import`. For an explicitly requested OpenSCAD project, OpenSCAD provides STL/3MF rendering; see [CAD exports](CAD.md).

## Updates and registrations

Close Fusion, Bionic and LM Studio before running `installupdate.sh`. It checks the new integrations and removes old managed release folders after the update succeeds. Generated documents and CAD outputs are preserved.

If Fusion previously used a script inside `releases/<old release>`, remove that obsolete registration using Fusion's controls and add the stable folder:

```text
~/Library/Application Support/Workshop/fusion/WorkshopDesign
```

Likewise, replace a Bionic skill pointing into an old release with:

```text
~/Library/Application Support/Workshop/Bionic/SKILL.md
```

Later updates refresh these stable folders, so they do not require registration against a new release directory.

## Troubleshooting

| What you see | What to do |
| --- | --- |
| No Utilities tab | Switch to Design, try Shift + S, or look for Scripts and Add-Ins in Fusion's command controls |
| Script list already open | Use its +/dropdown; you are already in the correct window |
| WorkshopDesign is absent | Add the folder containing the matching `.py` and `.manifest` files; clear search/type/source filters |
| Stable script folder is missing | Run the current updater, or locate the older successful release/source ZIP folder |
| Missing script after update | Replace the old release-folder registration with the stable path |
| File picker opens | Select the generated job JSON, not the script or raw example |
| Output must be a new .f3d filename | Request another output filename and prepare a new job |
| Missing output/units field | Use `prepare_fusion_design` to create a complete job |
| Unsupported primitive/operation | Use box/cylinder and new/join/cut only |
| Invalid dimensions/origin | Use positive finite dimensions and three finite origin coordinates |
| Cut/join fails | Check that the geometry intersects an existing body and that the first part is new |
| Export succeeds but file seems missing | Check `requested_output`, the success message and the result JSON; your workspace may be custom |
| Job is pending/queued | Run WorkshopBridge, finish active commands, or use WorkshopDesign manually; preparation alone cannot export F3D |
| Bridge offline | Register/run WorkshopBridge once and enable Run on Startup; check the configured queue directory matches |
| execution_unconfirmed | A run has no confirmed completion; inspect Fusion/output and use new filenames rather than replaying it |
| Error message/traceback | Copy the error and job details for diagnosis; do not assume the F3D completed |

For all Workshop capabilities, see the [full feature list](FEATURES.md). For installation details, see [Getting started](GETTING-STARTED.md).

## Native modelling and separate part files

Use `create_cad_project` with `backend: "fusion"` and named parts, each containing either a primitive `recipe` or native Python `source`. It creates a new folder, separate source/job/archive filenames per part and a `project.json` manifest. Native Python defines `build(design, root)`. The bridge supplies a new parametric document, executes native modelling APIs, checks for geometry and timeline errors, and exports the archive. `run_fusion_project` queues all parts; `fusion_project_status` reports each result and saved link. Separate files do not create an assembly automatically. Model a native assembly explicitly when needed.

For example, a recipe project argument is:

```json
{"folder":"bracket-v1","backend":"fusion","parts":[{"name":"base","recipe":{"parts":[{"kind":"box","width":40,"depth":30,"height":4}]}},{"name":"spacer","recipe":{"parts":[{"kind":"cylinder","diameter":12,"height":10}]}}],"notes":"Dimensions are mm. Independent parts; assembly placement not yet constrained."}
```

Then call `run_fusion_project` with `project_file: "bracket-v1/project.json"` and check `fusion_project_status` with that path. Each part reports its own success/failure. For a requested OpenSCAD project, choose `backend: "openscad"` and deliver/render its separate SCAD files instead. The tools never convert a failed Fusion project into OpenSCAD.

The model workflows include design intent, datums, units, constrained sketches, solid/surface features, topology selection, assemblies, tolerances, manufacturing constraints and validation. Guidance improves behaviour but cannot guarantee an arbitrary model's competence or the correctness of generated geometry. Review actual Fusion feature/shape results.

For a native script starting point, see [the filleted plate source](../examples/fusion_native_part.py). It defines `build(design, root)` for the native script tool, rather than a manually registered standalone script.
