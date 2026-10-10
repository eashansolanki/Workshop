# Set up Workshop

This guide takes you from downloading Workshop to using its integrations and exporting your first Fusion design. You do not need to compile code.

## 1. Download and install

Download `install.sh` from this repository or its GitHub release. If you downloaded `workshop.zip`, extract it and find `install.sh` inside the `workshop` folder.

1. Close LM Studio.
2. Open Terminal.
3. Type `bash `, including the space, then drag `install.sh` from Finder into Terminal. Press Return.
4. Confirm installation when prompted and wait for **Installation complete**.

Alternatively, from the folder containing the script:

```sh
bash install.sh
```

The installer downloads private Python and Node runtimes and Chromium, checks all eight integrations, backs up your LM Studio configuration and adds Workshop. The initial installation needs an internet connection. Keep the final output: it contains your Bionic skill path.

## 2. Use Workshop in LM Studio

1. Restart LM Studio.
2. Open its integrations/MCP controls and enable the Workshop integrations you want.
3. Use a model that supports tool calls.
4. Ask it to check capabilities and load the workflow for your task.

Example:

> Use Workshop's Excel integration. Check capabilities, load its workflow and create a monthly budget spreadsheet in my workspace.

Each integration covers one of the eight workflows listed in the [README](../README.md). The default output folder is `~/Documents/Workshop`.

## 3. Add Workshop to Bionic

1. Open **Settings → Skills → Add file** in Bionic.
2. Select the `SKILL.md` file whose full path was printed at the end of installation.
3. Ask Bionic to use Workshop for your task.

The installed skill hub contains all eight workflows and the runtime paths it needs. You do not need to add eight separate files when using this hub.

If you lost the printed path on macOS, open Finder, press **⌘ Shift G** and paste:

```text
~/Library/Application Support/Workshop
```

Open **Bionic → SKILL.md**. Older installations may have this file inside `releases/<release-folder>/Bionic`; running the updater creates the stable location above.

On Linux the default installation folder is `~/.local/share/workshop`, or `$XDG_DATA_HOME/workshop` when that variable is set. Custom installations use the directory specified by `WORKSHOP_HOME`.

For expanded Fusion instructions, folder locations, revisions and troubleshooting, see the [complete Fusion guide](FUSION360.md). For every supported tool, see the [full feature list](FEATURES.md).

## 4. Add the Fusion script once

Only do this if you want genuine `.f3d` design files. The shell installer does not register the script inside Fusion.

### Find the script folder

For an installed copy on macOS:

1. Open Finder and press **⌘ Shift G**.
2. Paste `~/Library/Application Support/Workshop`.
3. Open **fusion → WorkshopDesign**. Older installations have this inside `releases/<release-folder>` until updated.

If you downloaded and extracted the source ZIP, the same folder is at **workshop → fusion → WorkshopDesign**. Keep that extracted folder in a permanent location if you register its script in Fusion.

Select the **WorkshopDesign folder**, which contains both:

```text
WorkshopDesign/
├── WorkshopDesign.py
└── WorkshopDesign.manifest
```

The Python file is the script. The JSON recipe you will generate later is a separate input file.

### Register it in Fusion

1. Open Fusion and a design in the **Design** workspace.
2. Open **Utilities → Add-Ins → Scripts and Add-Ins**. You can also try **Shift + S** while Fusion is focused.
3. In that window, use **+** to add an existing script from your computer. In the list-style interface with a small **▼ beside +**, open that dropdown and choose the existing/local-script option. The wording varies by Fusion version.
4. Select the **WorkshopDesign folder** identified above.
5. Confirm that **WorkshopDesign** now appears in the list.

If you already see the window containing a list of scripts and a **+** at the top, you are already in the right place. You do not need to find Utilities again.

Autodesk documents the menu route and local-script registration in [Manage scripts and add-ins](https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-MANAGE-SCRIPTS-ADD-INS.htm).

## 5. Generate and export a Fusion design

In LM Studio or Bionic, ask:

> Use Workshop's OpenSCAD and Fusion workflow. Prepare a Fusion recipe for a plate measuring 40 × 30 × 4 mm with a 5 mm through-hole centred 10 mm from the left edge and 10 mm from the front edge. Save the recipe as plate-job.json and set the output to a new plate.f3d in my workspace. Show me the full recipe path.

Workshop should use `prepare_fusion_design` to create the job JSON. The preparation result is **pending** until Fusion runs it.

Then:

1. Return to Fusion's **Scripts and Add-Ins** window.
2. Select **WorkshopDesign** and click **Run**, or its **▶** button in the list-style interface.
3. In the file picker, choose the **generated job JSON** (`plate-job.json` in this example).
4. Wait for the script to finish.
5. Open the exported `plate.f3d` in Fusion and inspect its dimensions and geometry. A companion `.result.json` records the script result.

Use the JSON produced by `prepare_fusion_design`, rather than selecting the example recipe directly: the generated job includes the output path and units required by the script. Use a new output filename when rerunning; the script refuses to overwrite an existing F3D.

The bridge currently supports boxes, cylinders and new/join/cut operations. It runs inside installed Autodesk Fusion. Live F3D export remains unverified.

## Update Workshop later

Download the latest `installupdate.sh`, close LM Studio, Bionic and Fusion, and run `bash installupdate.sh`. It verifies the new tools before deleting old managed releases. Generated outputs and runtime downloads are preserved. Existing custom workspace and LM Studio configuration destinations are reused unless you provide explicit environment overrides.

If Bionic or Fusion references an old release directory, replace that registration once with the stable Bionic/Fusion paths printed by the updater. Future updates keep those paths. The updater contains a specific release; download it again when a new version is published.

## Optional tools

| What you want | Install separately |
| --- | --- |
| SCAD source | No additional application for source generation |
| STL, 3MF or PNG from SCAD | OpenSCAD |
| Legacy Word DOC or PDF conversion | LibreOffice |
| Native Pages, Numbers or Keynote files | The corresponding iWork apps on macOS |
| Genuine Fusion F3D files | Autodesk Fusion and the script registration above |

See the [CAD guide](CAD.md) for geometry and printing details. Numbers conversion remains unverified.

## If something goes wrong

| Problem | Next step |
| --- | --- |
| Workshop is missing in LM Studio | Confirm installation finished, restart LM Studio and check its MCP/integration controls |
| Bionic cannot find the tools | Add the installed `Bionic/SKILL.md` printed by the installer and keep its release directory in place |
| WorkshopDesign is missing in Fusion | Add the folder containing both the `.py` and `.manifest` files |
| Fusion cannot open the recipe | Select the job JSON returned by `prepare_fusion_design` |
| F3D export says the file exists | Prepare another job with a new `.f3d` filename |
| Installer fails | Inspect `setup.log` in the Workshop installation directory |

On macOS the default setup log is `~/Library/Application Support/Workshop/setup.log`. On Linux it is `~/.local/share/workshop/setup.log`, or beneath your configured data directory. Python and JavaScript tools run with your user permissions; execute only code you trust.

For developer configuration and release builds, use [source setup](../DEVELOPER-SETUP.md) and the [build guide](BUILDING.md).
