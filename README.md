# Paw Pads 3D Print Project

Custom 3D printable paw pads designed for shoes and attachments, tuned for Overture PLA on the Prusa MK4S.

## Design Specifications
- **Cluster Footprint:** ~50 mm × 50 mm (~2 inches overall area) placed near the toe/top of the shoe.
- **Components:** 5 discrete, disconnected objects:
  - `palm_pad.stl`: Main central 3-lobed palm bean (~32 mm × 24 mm × 4.5 mm height).
  - `toe_1_outer_left.stl`: Far-left toe bean, angled outward.
  - `toe_2_inner_left.stl`: Inner-left toe bean.
  - `toe_3_inner_right.stl`: Inner-right toe bean.
  - `toe_4_outer_right.stl`: Far-right toe bean, angled outward.
  - `paw_pad_complete_plate.stl`: Pre-arranged full 5-piece plate matching natural cluster spacing.
- **Top Profile:** Smooth quarter-sine domed organic profile (3.8 mm to 4.5 mm apex) for tactile feel and support-free FDM printing.

## Phases & Alignment
### Phase 1 (Active)
- **Base:** Flat planar back at $Z = 0$ for print bed adhesion on PEI sheets.

### Phase 2 (Planned - Converse Sole Integration)
- **Tread Pattern:** Authentic Converse Chuck Taylor All-Star diamond outsole pattern matching U.S. Trademark Reg. Nos. 1,588,960 and 3,258,103.
- **Geometry:**
  - $45^\circ$ crisscrossed diamond grid.
  - Pitch: $\approx 4.0\text{ mm} \times 6.0\text{ mm}$.
  - Groove width: $\approx 0.8\text{ mm}$.
  - Debossed depth: $\approx 0.8\text{ mm}$ channels into the bottom face.
- **Orientation:** All 5 pieces align to a shared continuous longitudinal grid vector matching the shoe's forward axis, maximizing adhesive surface area.

## Generation Script
The models are generated parametrically using Blender's headless Python engine via:
`generate_flat_paw_pads.py`
