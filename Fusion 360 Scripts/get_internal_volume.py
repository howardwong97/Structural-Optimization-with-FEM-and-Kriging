import adsk.core, adsk.fusion, adsk.cam, traceback
from math import sin, cos, pi, copysign
import csv

# Define key parameters here
A = 3.0 # radius of cylinder in cm
L = 7.0 # total length in cm
T = 0.1 # wall thickness in cm
m_values = [
    1.0,
    1.6166666666666667,
    1.1166666666666667,
    1.1833333333333333,
    1.05,
    1.15,
    1.3166666666666667,
    1.85,
    1.9166666666666667,
    1.9833333333333334,
    1.45,
    1.55,
    1.0833333333333333,
    1.35,
    1.7166666666666666,
    1.25,
    1.3833333333333333,
    1.65,
    1.75,
    1.2166666666666668,
    1.0166666666666666,
    1.8166666666666667,
    1.8833333333333333,
    1.2833333333333332,
    1.95,
    1.7833333333333332,
    1.6833333333333333,
    1.4833333333333334,
    1.5833333333333333,
    1.4166666666666667,
    1.5166666666666666
    ]

n_values = [
    1.0,
    0.94,
    1.1133333333333333,
    0.8466666666666667,
    1.0333333333333332,
    1.0466666666666666,
    0.9666666666666667,
    0.8733333333333334,
    1.1533333333333333,
    1.18,
    0.9266666666666666,
    0.98,
    1.0866666666666667,
    0.9933333333333334,
    1.0733333333333333,
    1.02,
    1.1,
    1.06,
    1.1400000000000001,
    1.1266666666666667,
    0.8333333333333334,
    0.86,
    1.0066666666666666,
    0.8066666666666668,
    0.8200000000000001,
    0.9533333333333334,
    0.9,
    1.1933333333333334,
    0.8866666666666667,
    1.1666666666666667,
    0.9133333333333333
]

# Functions to generate points
def X(theta, a, n):
    return abs(cos(theta)) ** (1 / n) * a * copysign(1, cos(theta))

def Y(theta, a, m, n):
    return abs(sin(theta)) ** (1 / n) * a / m * copysign(1, sin(theta))

def unit_norm(theta, a, m, n):
    gradX = 2 * n * X(theta, a, n)**(2 * n - 1)
    gradY = 2 * m * n * (m * Y(theta, a, m, n))**(2 * n - 1)
    magnitude = (gradX**2 + gradY**2)**0.5
    return gradX/magnitude, gradY/magnitude

SPLINE_POINTS = 50

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = app.activeProduct

        # Set display units as millimetres
        unitsMgr = design.fusionUnitsManager
        unitsMgr.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        
        volumes = []

        for M, N in zip(m_values, n_values):
            # Get the root component of the active design.
            rootComp = design.rootComponent

            # Create a new sketch on the xy plane.
            sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)

            # Create ObjectCollection to store point coordinates
            outer_points = adsk.core.ObjectCollection.create()
            inner_points = adsk.core.ObjectCollection.create()
            outer_points_opp = adsk.core.ObjectCollection.create()  # for opposite end
            inner_points_opp = adsk.core.ObjectCollection.create()

            L_cylinder = L - 2 * (A / M)

            # Generate points and add to collection
            for j in range(0, SPLINE_POINTS+1):
                phi = (j / SPLINE_POINTS) * pi/2
                x_norm, y_norm = unit_norm(phi, A, M, N)

                x_outer = X(phi, A, N)
                x_inner = x_outer - T * x_norm 
                
                y_outer = Y(phi, A, M, N)
                y_inner = y_outer - T * y_norm

                inner_points.add(adsk.core.Point3D.create(x_inner, 0, y_inner+L_cylinder/2))
                inner_points_opp.add(adsk.core.Point3D.create(x_inner, 0, -y_inner-L_cylinder/2))
            
            # Sketch splines
            inner_spline = sketch.sketchCurves.sketchFittedSplines.add(inner_points)
            inner_spline_opp = sketch.sketchCurves.sketchFittedSplines.add(inner_points_opp)        

            # Now we connect the splines with some lines
            lines = sketch.sketchCurves.sketchLines
            inner_cylinder_line = lines.addByTwoPoints(inner_spline.startSketchPoint, inner_spline_opp.startSketchPoint)
            
            # Doubles as final connecting line and rotation axis
            rotation_axis1 = lines.addByTwoPoints(inner_spline.endSketchPoint, inner_spline_opp.endSketchPoint)

            # Revolve feature
            profs = adsk.core.ObjectCollection.create()

            for prof in sketch.profiles:
                profs.add(prof)

            revolves = rootComp.features.revolveFeatures
            revInput = revolves.createInput(profs, rotation_axis1, adsk.fusion.FeatureOperations.NewComponentFeatureOperation)
            angle = adsk.core.ValueInput.createByReal(2 * pi)
            revInput.setAngleExtent(False, angle)
            ext = revolves.add(revInput)

            volumes.append(rootComp.physicalProperties.volume)
            
            # Delete everything
            newComponent = ext.parentComponent
            for occurence in rootComp.occurrencesByComponent(newComponent):
                occurence.deleteMe()
            sketch.deleteMe()
        
        with open('C:\\Users\\howar\\Desktop\\Final Pressure Vessel\\volumes.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["m", "n", "volume/cm3"])
            for m, n, v in zip(m_values, n_values, volumes):
                writer.writerow([m, n, v])
                

        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
