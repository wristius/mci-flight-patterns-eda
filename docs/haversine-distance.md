# Why haversine? How distance is measured in this project

This is the domain-knowledge note for the distance numbers in the
main README. It is kept separate so the README stays short, and so a
reader who does not know this coordinate system can understand why
the numbers are what they are.

## The coordinate system: latitude and longitude

Every airport in `data/airports.dat` is located by two numbers:

- **Latitude** — how far north or south of the equator, in degrees.
  Positive is north, negative is south. Kansas City (MCI) is at
  latitude 39.2976, meaning about 39.3 degrees north of the equator.
- **Longitude** — how far east or west of Greenwich, England, in
  degrees. Positive is east, negative is west. MCI is at longitude
  -94.7139, meaning about 94.7 degrees west.

So MCI is the point (39.2976, -94.7139). San Francisco (SFO) is
(37.619, -122.375). Those are **angles**, not miles. One degree of
latitude is about 69 miles everywhere. But one degree of longitude
is only about 69 miles at the equator — it shrinks as you move
toward the poles, because the lines of longitude converge. At
Kansas City's latitude (about 39 degrees north), one degree of
longitude is about 69 × cos(39°) ≈ 54 miles.

That is why you cannot just subtract the coordinates and treat the
result as a distance, the way you would on a flat map. A flat
calculation for MCI to San Francisco gives about 1,912 miles.
The real distance is 1,495 miles. The flat version is wrong by
almost 30%.

## Why haversine

The Earth is a sphere (very nearly — it is slightly squashed at the
poles, but a sphere is close enough here). The shortest path between
two points on a sphere is not a straight line through the Earth.
It is an arc along the surface, called a **great-circle** distance:
the "as-the-crow-flies" distance over the ground.

The **haversine formula** calculates exactly that great-circle
distance from two latitude/longitude pairs. It is the standard
choice for this job because:

1. It works directly on angles on a sphere, so it handles the
   shrinking longitude correctly.
2. It stays accurate even for short distances, where the older
   spherical law of cosines loses precision.
3. It is simple and well tested — one formula, no map projection
   needed.

## The formula

With φ = latitude in radians, λ = longitude in radians, and
R = Earth's radius:

```
a = sin²(Δφ/2) + cos φ1 · cos φ2 · sin²(Δλ/2)
c = 2 · atan2(√a, √(1−a))
d = R · c
```

In this project, R = 3,959 miles (Earth's mean radius in miles),
and the code is in `eda_mci.py` in the `haversine` function. The
angles are converted from degrees to radians before the trig
functions run, because trig functions in Python expect radians,
not degrees.

Worked example — MCI to San Francisco:

- MCI: latitude 39.2976, longitude -94.7139
- SFO: latitude 37.619, longitude -122.375
- Haversine distance: **1,495 miles** (the longest route in this
  dataset, and the number reported in the README)

## What this distance is, and is not

- It **is** the shortest distance over the Earth's surface between
  the two airports — the great-circle distance.
- It **is not** the distance a plane actually flies. Real flights
  follow airways, weather and air-traffic routing, so the flown
  distance is usually a little longer.
- It **is not** exact to the mile. The formula treats the Earth as
  a perfect sphere. The Earth is slightly ellipsoidal, and using a
  spherical model gives errors typically up to 0.3% — about 4 miles
  on a 1,495-mile route. That is small enough for an exploratory
  analysis, where the point is comparing routes, not navigating.

A more exact ellipsoidal formula (Vincenty) exists, but it is
more complex and would change these numbers by less than half a
percent. For this project, haversine is the right trade-off.

## Source

- Veness, Chris. "Calculate distance and bearing between two
  Latitude/Longitude points using haversine formula."
  Movable Type Scripts, https://www.movable-type.co.uk/scripts/latlong.html
  — the formula above, the statement that the haversine formula
  "remains particularly well-conditioned for numerical computation
  even at small distances", and the note that the spherical model
  gives errors "typically up to 0.3%".
- Airport coordinates: OpenFlights `data/airports.dat`, in this
  repository.
