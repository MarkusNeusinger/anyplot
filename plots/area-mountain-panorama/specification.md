# area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks

## Description

A panoramic mountain silhouette chart that renders the horizon as seen from a fixed vantage point, like a photograph of a ridgeline against the sky. A filled area under the skyline curve traces the ridgeline across a horizontal viewing range (in degrees of bearing or horizontal distance), and major summits are annotated with their name and elevation. Unlike an elevation-profile-along-a-trail, this plot is the angular view of the surrounding peaks from a single observer, making it ideal for summit-identification infographics, alpine panoramas, and travel guides.

## Applications

- Tourism and alpine-guide infographics: labeled summit panoramas from viewpoints, huts, or gondola stations (e.g., the classic Zermatt / Gornergrat view of the Matterhorn and surrounding 4000-m Wallis peaks)
- Mountaineering route planning: identifying summits visible from a given vantage point and orienting by bearing
- Geography and earth-science education: introducing real topography and ridgeline structure to students
- Travel blogs, hiking magazines, and ski-resort marketing: stylized horizon illustrations with named peaks
- Cross-section communication: visualizing the ridgeline profile along a travel path or compass sweep

## Data

- `angle_deg` (numeric) - horizontal viewing angle in degrees (compass bearing) or horizontal distance along the panorama
- `elevation_m` (numeric) - skyline elevation in meters at each angle sample
- `peaks` (list of objects) - summits to annotate, each with:
  - `name` (string) - peak name (e.g., "Matterhorn")
  - `angle_deg` (numeric) - horizontal position of the summit
  - `elevation_m` (numeric) - summit elevation in meters
- Size: ~500-2000 skyline sample points; 10-20 labeled peaks is typical
- Example: Wallis (Valais, Switzerland) panorama anchored on the Matterhorn, including Matterhorn (4478 m), Dent Blanche (4358 m), Ober Gabelhorn (4063 m), Zinalrothorn (4221 m), Weisshorn (4506 m), Dom (4545 m), Täschhorn (4491 m), Alphubel (4206 m), Allalinhorn (4027 m), Rimpfischhorn (4199 m), Strahlhorn (4190 m), Monte Rosa / Dufourspitze (4634 m), Liskamm (4527 m), Castor (4223 m), Pollux (4092 m), Breithorn (4164 m)

## Notes

- Fill the area below the ridgeline with a dark solid color (photo-like silhouette, evening/dusk feel)
- Optional sky-gradient background above the ridgeline (light blue → white, or dusk orange → deep blue) for a photographic mood
- Annotate each peak with a thin leader line from the summit up to a label; label format is peak name on top and elevation in meters below (e.g., "Matterhorn" / "4478 m")
- Stagger label vertical positions to avoid overlaps when peaks cluster; consider alternating heights or short offset columns
- Y axis in meters with a sensible lower bound (e.g., 2500 m) so the ridgeline occupies the upper portion of the plot
- X axis labels are optional: compass bearings (e.g., W, SW, S) or simply hidden — the panorama shape is the primary visual
- Equal aspect or slight vertical exaggeration is acceptable; prefer a wide aspect ratio (landscape) to feel panoramic
- The Matterhorn (or whichever anchor summit the data emphasizes) should read as visually prominent — it is the focal point of the composition
