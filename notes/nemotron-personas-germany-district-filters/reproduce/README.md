# Reproduce

## Recount without downloading anything

```
python3 -I src/check.py out
```

Standard library only. It reads the per-district counts in `out/` and prints every number in the note: rank
correlations and slopes, the national figures, the East German medians, the named districts and the two bounds for
people aged 20 and over (definitions in its docstring). It also writes `out/immigration-by-district.csv`. The bootstrap intervals and the within-state and age-adjusted slopes come from
`src/score.py` (below), which needs numpy and scipy.

## Files

- `Dockerfile`: Python 3.12 (pinned digest) with pinned geopandas, pyarrow, pandas, numpy and scipy.
- `src/ref.py`: census side. Assigns each 1 km grid cell to the district containing its centre and sums the counts
  per district. A cell counts for an attribute only if every number it needs is published (Destatis suppresses some
  cells).
- `src/frame.py`: dataset side. Reads only the structured fields (`uuid`, `kreis`, `bundesland`, `age`,
  `marital_status`, `migration_background`, `housing_tenure`, `household_type`), maps the 400 district names to
  official district codes, and stops if any name doesn't map to exactly one district or a category label is unexpected.
- `src/score.py`: rank correlation, slope with a district bootstrap (2,000 resamples, fixed seed 16679), slope within
  states, age-adjusted slope, split-half reliability, and the population-share control. `--selftest` runs planted
  datasets (district rates, national rates, state rates, age-only rates, a city and district with their record counts
  swapped, an attribute with no matches)
  and must print `selftest ok`.
- `src/check.py`: the recount above.
- `out/ref_kreis.csv`, `out/ds_kreis.csv`, `out/ds_kreis.map.csv`, `out/score.json`: the run's outputs.
  `out/immigration-by-district.csv`: written by `check.py`.
- `inputs.sha256`: SHA-256 of every input file, in the layout below.

## Full run

Inputs:

- Zensus 2022 1 km grid tables and district boundaries, from
  `https://www.destatis.de/static/DE/zensus/gitterdaten/<name>.zip` for these names:
  `Zensus2022_Bevoelkerungszahl`, `Zensus2022_Geburtsland_Gruppen_in_Gitterzellen`,
  `Eigentuemerquote_in_Gitterzellen`, `Familienstand_in_Gitterzellen`, `Typ_des_privaren_Haushalts_Lebensform`,
  `Alter_in_10er-Jahresgruppen`, `Shapefile_Zensus2022`. Put the zips in `ref/`, the `*_1km-Gitter.csv` file from
  each grid zip in `ref/grid1km/`, and `EPSG_25832/VG250_KRS.*` from `Shapefile_Zensus2022.zip` in
  `ref/vg/EPSG_25832/`.
- The dataset at revision `1285ad1810b157743056ae823aa609c770876b34`:
  `https://huggingface.co/datasets/nvidia/Nemotron-Personas-Germany/resolve/1285ad1810b157743056ae823aa609c770876b34/data/train-0000N-of-00010.parquet`
  for N = 0 to 9, saved as `data/train-0000N.parquet` (1.9 GB in total).

Check them with `sha256sum -c inputs.sha256`, then:

```
docker build -t personas-de-check .
docker run --rm --network none -v "$PWD/ref:/ref:ro" -v "$PWD/src:/src:ro" -v "$PWD/run:/out" personas-de-check \
  python -I /src/ref.py --grid /ref/grid1km --vg /ref/vg/EPSG_25832/VG250_KRS.shp --out /out/ref_kreis.csv
docker run --rm --network none -v "$PWD/ref:/ref:ro" -v "$PWD/data:/data:ro" -v "$PWD/src:/src:ro" -v "$PWD/run:/out" personas-de-check \
  python -I /src/frame.py --data /data --vg /ref/vg/EPSG_25832/VG250_KRS.shp --out /out/ds_kreis.csv
docker run --rm --network none -v "$PWD/src:/src:ro" -v "$PWD/run:/out" personas-de-check \
  python -I /src/score.py --ref /out/ref_kreis.csv --ds /out/ds_kreis.csv --out /out/score.json
```

On our machine the shipped `ref_kreis.csv` came from the first command, and the third command, run on the shipped
`out/` files, reproduces `out/score.json` byte for byte.

## Sources and licences

- Zensus 2022 1 km grid data: Statistisches Bundesamt (Destatis), Zensus 2022,
  https://www.destatis.de/static/DE/zensus/gitterdaten/ (files listed above), licensed under the
  [Datenlizenz Deutschland – Namensnennung – Version 2.0](https://www.govdata.de/dl-de/by-2-0). Modified: we summed
  the cell values per district (`out/ref_kreis.csv`) and computed the census columns of
  `out/immigration-by-district.csv` from those sums.
- District boundaries: VG250_KRS (as of 15 May 2022) from Destatis's `Shapefile_Zensus2022.zip` at the same address,
  © GeoBasis-DE / BKG 2022, licensed under the [Datenlizenz Deutschland – Namensnennung – Version
  2.0](https://www.govdata.de/dl-de/by-2-0). Used to assign grid cells to districts; the district codes, names and
  types in `out/` come from it. The boundary files themselves are not included.
- Nemotron-Personas-Germany: NVIDIA, https://huggingface.co/datasets/nvidia/Nemotron-Personas-Germany (revision
  `1285ad1810b157743056ae823aa609c770876b34`), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
  Modified: `out/ds_kreis.csv` and the dataset columns of `out/immigration-by-district.csv` are our per-district
  counts of its structured fields; `out/ds_kreis.map.csv` lists its district names with our district codes. No
  persona text is included.
- Our own code (`src/`, `Dockerfile`) and text: MIT (see `LICENSE`). The MIT licence does not cover the census or
  dataset material above, which stays under its own licence.
