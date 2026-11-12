# Eglinton Avenue East / Danforth Road: geometry review

Reviewed November 9, 2026 using Google Maps satellite imagery and Google Street View. The study location is TCS 379 at latitude 43.7370972916531, longitude -79.2461640653853, from the observed count records.

## Sources inspected

- [Google Maps satellite view](https://www.google.com/maps/@43.7370973,-79.2461641,146m/data=!3m1!1e3), also inspected at the 10 m scale.
- [June 2025 Street View at 2787 Eglinton Ave E](https://www.google.com/maps/@43.7371165,-79.245905,3a,75y,74.82h,90t/data=!3m4!1e1!3m2!1smIwtql5uqEU-sfuGrDJtNA!2e0).
- [April 2021 Street View at the same approach](https://www.google.com/maps/@43.7371136,-79.245899,3a,75y,74.82h,90t/data=!3m4!1e1!3m2!1sr0LTawwtzRxXVUl_6jBEmA!2e0).

The Street View dates were read from Google's date labels. At this selected panorama, the historical date selector listed June 2025, April 2021, September 2020, and older imagery; no 2024 panorama was shown in that list. This does not establish whether 2024 imagery exists elsewhere around the junction. The satellite footer's copyright year is not an acquisition date.

## Observations and comparison

| Feature | Google Maps observation | Existing prototype |
|---|---|---|
| Alignment | Four-arm skewed junction; roads meet obliquely and approaches are not aligned with the map's north/east axes | Orthogonal cross on north/south/east/west axes |
| Crosswalks | Zebra crosswalks are visible on all four arms | No crossing objects, sidewalks, or pedestrians |
| Medians and pockets | Raised median segments, tapered islands, and marked turning pockets are visible | Straight edges with the same three dedicated movement lanes on every approach |
| Curb lanes | Red-painted curb lanes are visible on Eglinton; the April 2021 eastward view and June 2025 eastward view both show the red lane | No separate transit lane permissions or restrictions |
| Local road detail | Curved corners and varied lane/edge layout | Symmetric, simplified connection geometry |
| Dimensions | Map scale supports orientation and rough visual checks | All arms set to 500 m and speeds to 13.89 m/s without field verification |

The observations establish that the current prototype is not a faithful site model. Exact inbound/outbound lane counts, shared-turn permissions, bus-lane operating rules, turn-bay storage lengths, lane widths, curve radii, and stop-line positions are not yet verified for every arm. No precise dimensions were inferred from these screenshots. No signal timing or 2024 operating plan was inferred from the imagery.

## Implications for the research model

1. Use TorontoSUMONetworks/City centreline or equivalent georeferenced source data to establish the skewed alignment, then reconcile lane and movement detail with the imagery and published drawings.
2. Verify each arm's lane assignments and turn-pocket storage individually; do not retain identical right/through/left lanes by default.
3. Add pedestrian sidewalks, crossing objects, stop lines, and compatible signal stages.
4. Verify transit-lane permissions and the layout applicable to the June and November 2024 count dates; the inspected 2021 and 2025 views bracket those dates but do not prove that nothing changed between them.
5. Revalidate the signal program against the new connections, then rerun the baseline on the frozen dev split. Existing numerical results remain results of the old idealized model.

This review did not modify the network, frozen split, signal program, or stored experimental results. The existing .sumocfg remains openable as a labeled prototype. The satellite tab was left open for the user.
