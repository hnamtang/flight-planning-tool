"""
Based on FAA Notice 8260.58A function "WGS84CrsIntersect"
"""

import math

import numpy as np

np.seterr(over="raise")
from geographiclib.geodesic import Geodesic

"""
    Compute the signed angular difference between two azimuths.
    
    Args:
        a1_deg (float): First azimuth angle in degrees
        a2_deg (float): Second azimuth angle in degrees
        
    Returns:
        float: Signed difference (a1 - a2) in radians, wrapped to (-π, π]
                                                                   
    Based on FAA Notice 8260.58A function "signedAzimuthDifference"                
"""


class SinVertexAngleZeroError(ValueError):
    """
    Raised when sine of the vertex angle is zero, which indicates a straight leg or U-turn leg.
    """

    pass


class RadiusError(ValueError):
    """
    Raised when for spherical triangle calculations, radius is greater than sphere radius
    multiplied by one half of vertex angle.
    """

    pass


def signed_azimuth_difference(a1_deg, a2_deg):
    a1 = a1_deg * math.pi / 180.0
    a2 = a2_deg * math.pi / 180.0

    d_az = (a1 - a2 + math.pi) % (2 * math.pi) - math.pi

    return d_az * 180.0 / math.pi


def find_linear_root(x, y):
    # Basic secant method for two points
    return x[0] - y[0] * (x[1] - x[0]) / (y[1] - y[0])


"""
   wgs84_crs_intersect

   Function:   This algorithm returns a true value if a point lies on and 
               within the bounds of a given geodesic. 
   
   Based on FAA Notice 8260.58A function "WGS84CrsIntersect"

   tol         =       Maximum error allowed in solution
"""


def wgs84_crs_intersect(pt1_lat, pt1_lon, crs13, pt2_lat, pt2_lon, crs23, tol):
    geod = Geodesic.WGS84
    a = geod.a
    f = geod.f
    b = a * (1 - f)
    SPHERE_radius = np.sqrt(a * b)

    # Step 1. Use inverse algorithm to calculate distance, azimuth and reverse
    # azimuth from pt1 to pt2.
    g = geod.Inverse(pt1_lat, pt1_lon, pt2_lat, pt2_lon)
    dist12 = g["s12"]
    crs12 = g["azi1"]
    temp = g["azi2"]
    crs21 = signed_azimuth_difference(
        temp, 180.0
    )  # Need course pointing towards the first point

    # Run a check to see if pt1 lies on the geodesic defined by pt2 and crs23
    # and if pt2 lies on the geodesic defined by pt1 and crs13
    # ADD LATER

    # Step 2. Calculate the signed azimuth difference in angle
    # between crs12 and crs13
    angle1 = signed_azimuth_difference(crs13, crs12)  # in degrees

    # Step 3. Calculate the signed azimuth difference in angle
    # between crs21 and crs23
    angle2 = signed_azimuth_difference(crs21, crs23)  # in degrees

    # Step 4. If sin(angle1)xsin(amgle2) < 0 then the courses lay on opposite
    # sides of the pt1-pt2 line and cannot intersect in this hemisphere.
    angle1 = np.deg2rad(angle1)
    angle2 = np.deg2rad(angle2)

    if np.sin(angle1) * np.sin(angle2) < 0:
        if abs(angle1) > abs(angle2):
            angle1 = (np.deg2rad(crs13) + np.pi) - np.deg2rad(crs12)
        else:
            angle2 = np.deg2rad(crs21) - (np.deg2rad(crs23) + np.pi)
        print("No intersection")

    angle1 = abs(angle1)
    angle2 = abs(angle2)

    # Apply the spherical triangle formulas to find the angle C and arc lengths
    # from A to C and from B to C - Appendix E - Section 3 - Paragraph 2
    C = np.arccos(
        -np.cos(angle1) * np.cos(angle2)
        + np.sin(angle1) * np.sin(angle2) * np.cos(dist12 / SPHERE_radius)
    )
    a_arc = SPHERE_radius * np.arccos(
        (np.cos(angle1) + np.cos(angle2) * np.cos(C)) / (np.sin(angle2) * np.sin(C))
    )
    b_arc = SPHERE_radius * np.arccos(
        (np.cos(angle2) + np.cos(angle1) * np.cos(C)) / (np.sin(angle1) * np.sin(C))
    )

    # Direct projection
    d = geod.Direct(pt1_lat, pt1_lon, crs13, np.rad2deg(b_arc))
    intx_lat = d["lat2"]
    intx_lon = d["lon2"]

    # Step 7. The following steps describe the function
    # iterateLineIntersection which is called once the initial approximation,
    # intx, of the line intersection is found

    # Step 8. Use the inverse algorithm to calculate dist13,
    # the distance from pt1 to intx.
    g = geod.Inverse(pt1_lat, pt1_lon, intx_lat, intx_lon)
    dist13 = g["s12"]

    # Step 9. Use the inverse algorithm to calculate dist23, the distance
    # from pt2 to intx.
    g = geod.Inverse(pt2_lat, pt2_lon, intx_lat, intx_lon)
    dist23 = g["s12"]

    if dist13 < tol or dist23 < tol:
        print("Problem: intersection too close to original point")

    # Step 12. Swap if necessary
    if dist23 < dist13:
        pt1_lat_temp = pt1_lat
        pt1_lon_temp = pt1_lon

        pt1_lat = pt2_lat
        pt1_lon = pt2_lon

        pt2_lat = pt1_lat_temp
        pt2_lon = pt1_lon_temp

        crs13_temp = crs13
        crs13 = crs23
        crs23 = crs13_temp

        dist13 = dist23

        swapped = 1

        # Step 13

    # Step 14. Initialize the distance array
    distarray = [dist13]

    # Step 15. Use the direct algorithm to project intx onto the geodesic from pt1
    d = geod.Direct(pt1_lat, pt1_lon, crs13, dist13)
    intx_lat = d["lat2"]
    intx_lon = d["lon2"]

    # Step 16. Use the inverse algorithm to measure the azimuth acrs23 from pt2 to intx
    acrs23 = np.deg2rad(geod.Inverse(pt2_lat, pt2_lon, intx_lat, intx_lon)["azi1"])

    # Step 17. Initialize the error array:
    errarray = [signed_azimuth_difference(acrs23, crs23)]

    # Step 18. Initialize the second element of the distance array using a
    # logical guess
    distarray.append(1.01 * dist13)

    # Step 19. Use the direct algorithm to project the second approximation
    # of intx onto the geodesic from pt1
    d = geod.Direct(pt1_lat, pt1_lon, crs13, distarray[1])
    intx_lat = d["lat2"]
    intx_lon = d["lon2"]

    # Step 20. Use the inverse algorithm to measure the azimuth acrs23
    # from pt2 to intx
    acrs23 = geod.Inverse(pt2_lat, pt2_lon, intx_lat, intx_lon)["azi1"]

    # Step 21. Initialize the error array
    errarray.append(signed_azimuth_difference(acrs23, crs23))

    # Step 22. Initialize k
    k = 0
    error = 9999
    maxIterationCount = 100

    # Step 23. Do while (k=0) or (error > tol) and (k < maxIterationCount)
    while error > tol and k < maxIterationCount:
        # (a) Use linear approximation to find root of errarray as a function of distarray.
        dist13 = find_linear_root(distarray, errarray)

        # (b) Use the direct algorithm to project the next approximation
        # of the intersection point, newPt, onto the geodesic from pt1
        d = geod.Direct(pt1_lat, pt1_lon, crs13, dist13)

        newPt_lat = d["lat2"]
        newPt_lon = d["lon2"]

        # (c) Use inverse algorithm to calculate the azimuth acrs23 from pt2 to intx.
        g = geod.Inverse(pt2_lat, pt2_lon, newPt_lat, newPt_lon)
        acrs23 = g["azi1"]

        # (d) Use the inverse algorithm to compute the distance from newPt
        # to intx (the previous estimate).
        error = geod.Inverse(newPt_lat, newPt_lon, intx_lat, intx_lon)["s12"]

        # (e) Update distarray and errarray with new values
        distarray[0], errarray[0] = distarray[1], errarray[1]
        distarray[1] = dist13
        errarray[1] = signed_azimuth_difference(acrs23, crs23)

        intx_lat = newPt_lat
        intx_lon = newPt_lon

        # (f) increment
        k += 1

    g1 = geod.Inverse(pt1_lat, pt1_lon, intx_lat, intx_lon)
    g2 = geod.Inverse(pt2_lat, pt2_lon, intx_lat, intx_lon)
    crs31 = g1["azi2"]
    crs32 = g2["azi2"]

    # Step 25. Check if k is maximum
    if k == maxIterationCount:
        print("Solution may not have converged")

    return intx_lat, intx_lon, crs31, crs32


"""
    Compute a circular arc tangent to two geodesics, using a fixed radius.
    
    Parameters:
        pt1: dict with 'lat' and 'lon' in radians - start point on first geodesic
        crs12: float - forward azimuth from pt1 along first geodesic (radians)
        pt3: dict with 'lat' and 'lon' in radians - point on second geodesic
        crs3: float - unused but included for compatibility
        crs3_inv: float - reverse azimuth for second geodesic at pt3 (radians)
        radius: float - arc radius in meters
    
    Returns:
        centerPt: dict with lat/lon of arc center (radians)
        startPt: dict with lat/lon of arc tangent on first geodesic (radians)
        endPt: dict with lat/lon of arc tangent on second geodesic (radians)
        dir: +1 for left turn, -1 for right turn, 0 for no valid arc
"""


def wgs84_tangent_fixed_radius_arc(
    pt1_lat, pt1_lon, crs12, pt3_lat, pt3_lon, crs3_further, radius
):
    geod = Geodesic.WGS84
    # Constants for WGS-84
    a = 6378137.0
    f = 1 / 298.257223563
    b = a * (1 - f)
    SPHERE_radius = np.sqrt(a * b)

    tol = 1e-3

    # Step 1. Find the intersection point of two geodesics
    pt2_lat, pt2_lon, crs21, crs23 = wgs84_crs_intersect(
        pt1_lat, pt1_lon, crs12, pt3_lat, pt3_lon, crs3_further, tol
    )

    if pt2_lat is None:
        print("Could not find an intersection point")
        return empty_result()

    # Step 4. Compute distance from pt1 to pt2
    g = geod.Inverse(pt1_lat, pt1_lon, pt2_lat, pt2_lon)
    dist12 = g["s12"]
    temp = g["azi2"]  # Final azimuth (degrees at destination)
    crs21 = signed_azimuth_difference(temp, 180.0)

    # Step 5. Compute azimuth from pt2 to pt3
    g = geod.Inverse(pt2_lat, pt2_lon, pt3_lat, pt3_lon)
    crs23 = g["azi1"]
    temp = g["azi2"]  # Final azimuth (degrees at destination)
    crs32 = signed_azimuth_difference(temp, 180.0)

    # Step 6. Angle between courses at pt2
    vertexAngle = np.deg2rad(signed_azimuth_difference(crs23, crs21))

    # Step 7. Check for trivial turn (straight or U-turn)
    if abs(np.sin(vertexAngle)) < tol:
        print("Nothing to return")
        return empty_result()

    # Step 8-9. Determine arc direction
    direction = 1 if vertexAngle > 0 else -1

    # Step 11. Spherical triangle calculations
    B = abs(vertexAngle / 2.0)

    # Step 11b. Check feasibility
    if radius > abs(SPHERE_radius * B):
        print("No arc possible - empty result")
        return empty_result()

    # Step 11d. Approximate distance from pt2 to tangent points
    distToStart = SPHERE_radius * np.arcsin(np.tan(radius / SPHERE_radius) / np.tan(B))

    # Step 12-13. Initialize loop
    k = 0
    error = 0.0
    maxIterationCount = 100

    while k == 0 or (abs(error) > tol and k < maxIterationCount):
        # (a) Update distance estimate
        distToStart += error / np.sin(vertexAngle)

        # (b) Project from pt2 along crs21
        d = geod.Direct(pt2_lat, pt2_lon, crs21, distToStart)
        startPt_lat = d["lat2"]
        startPt_lon = d["lon2"]

        # (c) Compute reverse azimuth from startPt to pt2
        g = geod.Inverse(startPt_lat, startPt_lon, pt2_lat, pt2_lon)
        perpCrs = g["azi1"]

        # (d-e) Adjust azimuth by 90° left or right
        if direction < 0:
            perpCrs += 90.0
        else:
            perpCrs -= 90.0

        # (g) Project arc center from startPt
        d = geod.Direct(startPt_lat, startPt_lon, perpCrs, radius)
        centerPt_lat = d["lat2"]
        centerPt_lon = d["lon2"]

        # (h) Project arc center to second geodesic
        (endPt_lat, endPt_lon, crsFromPoint, perpDist) = wgs84_perp_intercept(
            pt3_lat, pt3_lon, crs32, centerPt_lat, centerPt_lon, 1e-9
        )

        # (i) Compute tangency error
        error = radius - perpDist
        k += 1

    return (
        centerPt_lat,
        centerPt_lon,
        startPt_lat,
        startPt_lon,
        endPt_lat,
        endPt_lon,
        direction,
    )


# Helper: Return empty values
def empty_result():
    return (
        {"lat": np.nan, "lon": np.nan},
        {"lat": np.nan, "lon": np.nan},
        {"lat": np.nan, "lon": np.nan},
        0,
    )


"""
    Determines the perpendicular (closest) intercept point from pt3 to the geodesic starting at pt1 along crs12.
    Based on FAA Notice 8260.58A (WGS84PerpIntercept).
"""


def wgs84_perp_intercept(pt1_lat, pt1_lon, crs12, pt3_lat, pt3_lon, tol):
    geod = Geodesic.WGS84

    # Constants
    a = 6378137.0
    f = 1 / 298.257223563
    b = a * (1 - f)
    SPHERE_radius = math.sqrt(a * b)

    # Step 1: Inverse geodesic from pt1 to pt3
    g = geod.Inverse(pt1_lat, pt1_lon, pt3_lat, pt3_lon)
    dist13 = g["s12"]
    crs13 = g["azi1"]
    temp = g["azi2"]  # Final azimuth (degrees at destination)
    crs31 = signed_azimuth_difference(temp, 180.0)

    # Step 2: Azimuth difference between given geodesic and pt1→pt3
    da = np.deg2rad(abs(signed_azimuth_difference(crs13, crs12)))

    # Step 3: Handle near-zero distance
    if dist13 <= tol:
        return pt1_lat, pt1_lon, crs31, dist13

    # Step 4: Handle near-parallel lines (angle ≈ 90 deg)
    if (math.pi / 2.0 - da) < tol:
        B = da
        A = math.pi / 2
        a_ = dist13 / SPHERE_radius
        b_ = math.asin(math.sin(B) * math.sin(a_))
        dist12 = (
            2.0
            * SPHERE_radius
            * math.atan(math.tan(0.5 * (a_ - b_)))
            * math.sin(0.5 * (A + B))
            / math.sin(0.5 * (A - B))
        )

        if abs(dist12) < tol:
            return pt1_lat, pt1_lon, crs31, dist13

        # Step 4(g): Project backward along crs12
        d = geod.Direct(pt1_lat, pt1_lon, crs12 + 180.0, 1.1 * dist12)
        newPt1_lat = d["lat2"]
        newPt1_lon = d["lon2"]

        # Step 4(h): Update geodesic course
        # Step 1: Inverse geodesic from pt1 to pt3
        g = geod.Inverse(newPt1_lat, newPt1_lon, pt1_lat, pt1_lon)
        crs12 = g["azi1"]

        pt1_lat = newPt1_lat
        pt1_lon = newPt1_lon

    # Step 5: Estimate initial perpdistendicular intercept distance
    B = da
    A = math.pi / 2
    a_ = dist13 / SPHERE_radius
    b_ = math.asin(math.sin(B) * math.sin(a_))
    dist12 = (
        2.0
        * SPHERE_radius
        * math.atan(math.tan(0.5 * (a_ - b_)))
        * math.sin(0.5 * (A + B))
        / math.sin(0.5 * (A - B))
    )

    # Step 6: Project pt2 from pt1
    d = geod.Direct(pt1_lat, pt1_lon, crs12, dist12)
    pt2_lat = d["lat2"]
    pt2_lon = d["lon2"]

    # Step 7 & 8: Get course and distance from pt2 to pt1 & pt3
    g = geod.Inverse(pt1_lat, pt1_lon, pt2_lat, pt2_lon)
    temp = g["azi2"]  # Final azimuth (degrees at destination)
    crs21 = signed_azimuth_difference(temp, 180.0)

    g = geod.Inverse(pt2_lat, pt2_lon, pt3_lat, pt3_lon)
    dist23 = g["s12"]
    crs23 = g["azi1"]

    # Step 9: Initial azimuth angle difference
    da = np.deg2rad(abs(signed_azimuth_difference(crs21, crs23)))

    # Step 10–11: Initial error and distance arrays
    errarray = [da - math.pi / 2.0]
    distarray = [dist12]

    # Step 12–13: Second guess
    distarray.append(distarray[0] + errarray[0] * dist23)

    d = geod.Direct(pt1_lat, pt1_lon, crs12, distarray[1])
    pt2_lat = d["lat2"]
    pt2_lon = d["lon2"]

    # Step 14–16: Recalculate azimuth and error
    g = geod.Inverse(pt1_lat, pt1_lon, pt2_lat, pt2_lon)
    temp = g["azi2"]  # Final azimuth (degrees at destination)
    crs21 = signed_azimuth_difference(temp, 180.0)

    g = geod.Inverse(pt2_lat, pt2_lon, pt3_lat, pt3_lon)
    crs23 = g["azi1"]

    errarray.append(
        np.deg2rad(abs(signed_azimuth_difference(crs21, crs23))) - math.pi / 2.0
    )

    # Step 17: Iteration setup
    error = 9999
    k = 0
    maxIterationCount = 100

    # Step 18: Iterate to refine
    while error > tol and k < maxIterationCount:
        dist12 = find_linear_root(distarray, errarray)

        d = geod.Direct(pt1_lat, pt1_lon, crs12, dist12)
        pt2_lat = d["lat2"]
        pt2_lon = d["lon2"]

        g = geod.Inverse(pt1_lat, pt1_lon, pt2_lat, pt2_lon)
        temp = g["azi2"]  # Final azimuth (degrees at destination)
        crs21 = signed_azimuth_difference(temp, 180.0)

        g = geod.Inverse(pt2_lat, pt2_lon, pt3_lat, pt3_lon)
        dist23 = g["s12"]
        crs23 = g["azi1"]
        temp = g["azi2"]  # Final azimuth (degrees at destination)
        crs32 = signed_azimuth_difference(temp, 180.0)

        distarray[0] = distarray[1]
        errarray[0] = errarray[1]
        distarray[1] = dist12
        errarray[1] = (
            np.deg2rad(abs(signed_azimuth_difference(crs21, crs23))) - math.pi / 2.0
        )
        error = abs(distarray[1] - distarray[0])
        k += 1

    # Step 20–22: Finalize
    crsFromPoint = crs32
    distFromPoint = dist23

    if pt2_lon > 180.0:
        pt2_lon -= 360.0

    return pt2_lat, pt2_lon, crsFromPoint, distFromPoint


def wgs84_tangent_fixed_radius_flyby_arc(
    pt1_lat, pt1_lon, pt2_lat, pt2_lon, pt3_lat, pt3_lon, radius
):
    geod = Geodesic.WGS84
    # Constants for WGS-84
    a = 6378137.0
    f = 1 / 298.257223563
    b = a * (1 - f)
    SPHERE_radius = np.sqrt(a * b)

    tol = 1e-3

    # Step 4. Compute azimuth from pt1 to pt2
    g = geod.Inverse(pt1_lat, pt1_lon, pt2_lat, pt2_lon)
    dist12 = g["s12"]
    temp = g["azi2"]  # Final azimuth (degrees at destination)
    crs21 = signed_azimuth_difference(temp, 180.0)

    # Step 5. Compute azimuth from pt2 to pt3
    g = geod.Inverse(pt2_lat, pt2_lon, pt3_lat, pt3_lon)
    crs23 = g["azi1"]
    temp = g["azi2"]  # Final azimuth (degrees at destination)
    crs32 = signed_azimuth_difference(temp, 180.0)

    # Step 6. Angle between courses at pt2
    vertexAngle_deg = signed_azimuth_difference(crs23, crs21)
    vertexAngle = np.deg2rad(vertexAngle_deg)

    # Step 7. Check for trivial turn (straight or U-turn)
    if abs(np.sin(vertexAngle)) < tol:
        # print("Nothing to return")
        # return empty_result()
        raise SinVertexAngleZeroError("Leg is straight or U-turn")

    # Step 8-9. Determine arc direction
    if vertexAngle > 0:
        direction = 1
    else:
        direction = -1

    # Step 11. Spherical triangle calculations
    B = abs(vertexAngle / 2.0)

    # Step 11b. Check feasibility
    if radius > abs(SPHERE_radius * B):
        # print("No arc possible - empty result")
        # return empty_result()
        raise RadiusError("No arc possible")

    # Step 11d. Approximate distance from pt2 to tangent points
    distToStart = SPHERE_radius * np.arcsin(np.tan(radius / SPHERE_radius) / np.tan(B))

    # Step 12-13. Initialize loop
    k = 0
    error = 0.0
    maxIterationCount = 100

    while k == 0 or (abs(error) > tol and k < maxIterationCount):
        # (a) Update distance estimate
        distToStart += error / np.sin(vertexAngle)

        # (b) Project from pt2 along crs21
        d = geod.Direct(pt2_lat, pt2_lon, crs21, distToStart)
        startPt_lat = d["lat2"]
        startPt_lon = d["lon2"]

        # (c) Compute reverse azimuth from startPt to pt2
        g = geod.Inverse(startPt_lat, startPt_lon, pt2_lat, pt2_lon)
        perpCrs = g["azi1"]

        # (d-e) Adjust azimuth by 90° left or right
        if direction < 0:
            perpCrs += 90.0
        else:
            perpCrs -= 90.0

        # (g) Project arc center from startPt
        d = geod.Direct(startPt_lat, startPt_lon, perpCrs, radius)
        centerPt_lat = d["lat2"]
        centerPt_lon = d["lon2"]

        # (h) Project arc center to second geodesic
        (endPt_lat, endPt_lon, crsFromPoint, perpDist) = wgs84_perp_intercept(
            pt3_lat, pt3_lon, crs32, centerPt_lat, centerPt_lon, 1e-9
        )

        # (i) Compute tangency error
        error = radius - perpDist
        k += 1

    return (
        centerPt_lat,
        centerPt_lon,
        startPt_lat,
        startPt_lon,
        endPt_lat,
        endPt_lon,
        direction,
    )


# Helper: Return empty values
def empty_result():
    return (
        {"lat": np.nan, "lon": np.nan},
        {"lat": np.nan, "lon": np.nan},
        {"lat": np.nan, "lon": np.nan},
        0,
    )
