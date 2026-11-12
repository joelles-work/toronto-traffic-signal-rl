# Eglinton–Danforth geometry revision

Open `Eglinton_Danforth.sumocfg` in the project root, or double-click `Open_SUMO_Intersection.cmd`. The old `Eglinton_Danforth_Prototype.sumocfg` is retained as the original experimental model.

This revision uses a georeferenced OpenStreetMap extract, compared visually with Google Maps. The source map data and lane tags replace the old orthogonal cross. It has sidewalks, a full-width pedestrian crossing on each arm, distinct carriageways, and explicit vehicle movement connections. The demonstration pedestrians have been replaced with all 518 observed dev-period pedestrians. Each 15-minute leg total is preserved; within-interval arrival times, direction balance, and walking speed remain modeled.

The right/east arm now uses separate eastbound and westbound nodes. Opposite carriageways no longer share the intermediate junctions that incorrectly paved over their median. Their shared road spine comes from the source map. A 2.4 m median is an explicit modeling assumption, not a surveyed dimension. Red curb overlays are visual only; legal transit-lane restrictions still need verification.

Rebuild using `rebuild_intersection.py`. The original downloaded `source/site.osm.xml` is preserved. Derived plain XML files document the geometry edits, including the separate eastbound/westbound nodes. `provenance.json` records the source hash, lane counts, and modeling assumptions.

The signal program passed conflict and clearance checks, and an actual 7,200-step trace verified 60 cycles and all 518 pedestrians using the intended signalized crossing. Five dev runs completed all 3,594 vehicles and 518 pedestrians, with no collisions or teleports; emergency-braking events were recorded and remain in the evidence. See `evidence/SIGNAL_AND_DEMAND_CHECK.md` for final metrics and limitations. This verifies the implemented simulation, not historical 2024 fidelity or field calibration. The old progress report still documents the earlier vehicle-only prototype.

Map data © OpenStreetMap contributors. Data and derived map geometry are available under the Open Database License 1.0: https://www.openstreetmap.org/copyright and https://opendatacommons.org/licenses/odbl/1-0/ . Google Maps imagery was used for comparison, not traced into the data.
