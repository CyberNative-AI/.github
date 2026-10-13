# Map sources

`natrf2022-gap-map.png` and `natrf2022-gap-map.svg` show the bare `cs2cs EPSG:6318 EPSG:10968` vs NCAT gap (`per_point[id].A1` in `../out/results.json`, metres) at the 230 points in `../data/frame.json`. They add no data: `make_map.py` re-reads the SVG it writes and stops unless every plotted value equals `results.json` exactly and every dot sits at its `frame.json` coordinates.

## Boundaries

- File: `cb_2025_us_state_20m.zip`, U.S. Census Bureau 2025 cartographic boundary file, states, 1:20,000,000, downloaded October 13, 2026 from <https://www2.census.gov/geo/tiger/GENZ2025/shp/cb_2025_us_state_20m.zip>
- SHA-256: `9340b6d995e971b2b4230518f4fa85e6cd9e7fe6811afabc90a6a8b1191530f6` (checked by `make_map.py`)
- Terms, from the file's metadata: "These products are free to use in a product or publication, however acknowledgement must be given to the U.S. Census Bureau as the source. The boundary information is for visual display at appropriate small scales only." The map credits the Census Bureau and uses the file only as a national overview, about 1:25,000,000 at the README display width of 760 pixels.
- Drawn: the lower 48 states and DC, and Alaska. Hawaii and Puerto Rico are not in the sample and are not drawn.

## Drawing

- Projections: Albers equal-area conic on GRS80 with the EPSG:5070 parameters for the lower 48 and the EPSG:3338 parameters for Alaska, both at the same nominal scale.
- Classes, in metres, lower bound inclusive: 0.09, 0.12, 0.15, 0.18, 0.30, 0.60. Colour is one hue stepped evenly in lightness; dot size repeats the class. Dots are drawn smallest gap first, so where dots overlap the larger gap is on top; every dot keeps at least 30% of its area visible (asserted).
- `python3 -I make_map.py` writes the SVG and runs the checks with the Python standard library only. `python3 -I make_map.py --png` also renders the PNG at 2x with headless Google Chrome and reduces it to its 256 most frequent colours with Pillow, then checks that the dot centres keep their exact class colours.
