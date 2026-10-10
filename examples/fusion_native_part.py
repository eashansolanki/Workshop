"""Native Fusion example for prepare_fusion_script's source argument.

Build a 40 x 30 x 4 mm plate with 1 mm edge fillets. Workshop supplies a new
design/root, validates feature health and performs the archive export.
This example requires live Fusion verification; it is not a mesh workaround.
"""
import adsk.core
import adsk.fusion


def build(design, root):
    # User parameters drive the CAD history; coordinates only seed the sketch.
    for name, expression, reason in (
        ("width", "40 mm", "Requested footprint width"),
        ("depth", "30 mm", "Requested footprint depth"),
        ("thickness", "4 mm", "Requested spacer thickness"),
        ("edge_radius", "1 mm", "Assumed handling-edge rounding; confirm preference"),
    ):
        if not design.userParameters.add(
                name, adsk.core.ValueInput.createByString(expression), "mm", reason):
            raise RuntimeError("Could not create parameter " + name)
    if design.userParameters.itemByName("edge_radius").value * 2 >= design.userParameters.itemByName("thickness").value:
        raise ValueError("Edge radius must leave a positive straight section through the thickness")
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = "Plate footprint (40 x 30 mm)"
    rectangle = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        sketch.originPoint, adsk.core.Point3D.create(4, 3, 0))
    if not rectangle or rectangle.count != 4:
        raise RuntimeError("Plate rectangle creation failed")
    # Find the opposing corner without depending on the returned edge order.
    opposite = None
    for index in range(rectangle.count):
        line = rectangle.item(index)
        for point in (line.startSketchPoint, line.endSketchPoint):
            if point.geometry.x > 0 and point.geometry.y > 0:
                opposite = point
    if opposite is None:
        raise RuntimeError("Plate rectangle is missing its opposite corner")
    dimensions = sketch.sketchDimensions
    horizontal = dimensions.addDistanceDimension(
        sketch.originPoint, opposite,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(2, -0.5, 0))
    vertical = dimensions.addDistanceDimension(
        sketch.originPoint, opposite,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(-0.5, 1.5, 0))
    if not horizontal or not vertical:
        raise RuntimeError("Could not dimension the plate footprint")
    horizontal.parameter.expression = "width"
    vertical.parameter.expression = "depth"
    if not sketch.isFullyConstrained:
        raise RuntimeError("Footprint is underconstrained; repair its datum or dimensions before exporting")
    if sketch.profiles.count != 1:
        raise RuntimeError("Plate footprint must have one closed profile")
    extrudes = root.features.extrudeFeatures
    extrusion = extrudes.createInput(
        sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString("thickness"))
    if not extrusion.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection):
        raise RuntimeError("Plate thickness extent failed")
    plate = extrudes.add(extrusion)
    plate.name = "Plate thickness (4 mm)"
    body = plate.bodies.item(0)
    body.name = "Filleted plate"
    edges = adsk.core.ObjectCollection.create()
    for index in range(body.edges.count):
        edges.add(body.edges.item(index))
    fillets = root.features.filletFeatures
    fillet = fillets.createInput()
    fillet.edgeSetInputs.addConstantRadiusEdgeSet(
        edges, adsk.core.ValueInput.createByString("edge_radius"), True)
    finishing = fillets.add(fillet)
    finishing.name = "Edge fillets (1 mm)"
    sketch.isVisible = False
