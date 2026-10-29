# AMENDMENT-SD-01 (written 2026-10-29T07:26:24Z, AFTER out/sd-result.json was read)

The pre-registered verdict is unchanged: CONTINUE. NEAREST Z_count is 0.195 (10-15) and 0.183 (10-19), both >= 0.10.
C1, C2 and C3 pass. out/sd-result.json is kept unedited.

Post-result changes, all disclosed:
1. **Bug fix, secondary metric.** sd_census.py computed depth_cm = sd/rsn*100. The correct formula is
   sd[m we]*1000/rsn[kg m-3]*100. So every depth figure in sd-result.json is 1000x too small, and
   share_depth_change_ge5cm = 0 is wrong. Z and the sd-based metrics do not use rsn and are unaffected.
2. **Post-hoc split.** The pre-change snow quantiles show that >= 50 % of "snow" land points sit at the 10 m we glacier
   cap (Antarctica, Greenland). They dilute Z. sd_census_a1.py adds a SEASONAL subset (0.001 <= sd16 < 9.9 m) and a
   30-70N band. These figures are post-hoc and are labelled so wherever they are used. The decision rests only on the
   pre-registered Z.
3. Same image, inputs (RAW-SD.sha256) and arms. The code is a copy of sd_census.py with these changes only.
