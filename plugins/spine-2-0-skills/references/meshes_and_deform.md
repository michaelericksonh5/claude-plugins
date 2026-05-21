# Meshes, Weights, and Deform

When to mesh, how to think about vertex placement, how weights bind bones to vertices, when deform keys are appropriate (almost never), and how the JSON contract looks. Distilled from the official Spine documentation on mesh attachments, weights, and deform timelines, with the slot-machine context grafted on top.

## Region vs mesh — the decision

A region attachment is a textured rectangle moved by one bone. A mesh attachment is a textured polygon whose vertices can move individually.

| Need | Use | Why |
|---|---|---|
| Symbol body that only translates/rotates/scales as a whole | Region | Cheapest. One quad, one matrix. |
| Frame, glow, sparkle decoration | Region | No deformation needed; the whole image moves together. |
| LP letter, JP badge, value text | Region | Static art; idle is just scale pulse. |
| Avatar state-graph frame (one PNG per state) | Region | Each state is a separate slot; no per-vertex motion within a state. |
| Character body that needs to bend (a tail curling, body squashing past simple scale) | Mesh | Deformation is the whole point. |
| Cape, flag, hair that should react to motion | Mesh | Needs bones-along-the-length and weights. |
| Large asset with lots of transparent margin (e.g., a frame_glow that's 90% blank) | Mesh with trimmed hull | Pixels outside the mesh hull never render — saves fill rate. |
| Small asset, fully opaque rectangle | Region | Meshing a rectangle wastes vertex transforms with no benefit. |

The official mesh doc puts the cost trade clearly: *"each vertex must be computed by the CPU each frame. This is a fast operation, but many skeletons on screen at once with many meshes, each having many vertices, can add up to thousands of positions that need to be computed."* Slot games run many symbols simultaneously, so meshing should be reserved for content that visibly benefits.

## Vertex placement — the decisions an animator makes

These are not automatable; they require an animator's eye and an iteration loop with the result. The skill's job is to flag candidates and document the principles, not to place vertices.

**Hull placement** — the outer boundary of the mesh.

- Trace tight to the visible art. Pixels outside the hull don't render.
- For art with concavities (e.g. an arm with a gap between body and limb), the hull can be concave but cannot have holes. Holes inside the mesh require either two meshes around the hole or transparent pixels in the source image.
- If the hull edge cuts through non-transparent pixels, the cut edge will alias. MSAA at runtime can soften it; or pad the source image with a couple of transparent pixels at the boundary so the edge has alpha to interpolate.

**Interior vertices** — placed at features that need to bend independently.

- A nose-bridge vertex isolates nose deformation from cheek deformation (the official doc walks through this example exactly).
- A wrist vertex separates hand deformation from forearm.
- Vertices that share triangle edges with each other deform together; manual edges (orange in the editor) force triangulation that respects the artist's intent.

**Vertex count** — the cost lever.

- Each vertex = one vertex transform per frame.
- Each weight-bound bone per vertex = one additional vertex transform.
- A 100-vertex mesh with 2-bone weights = 200 vertex transforms per frame, per instance of that mesh.
- The `Prune` tool removes weights below a threshold and caps bones-per-vertex.

The bundled helper `scripts/trace_mesh_hull.py` can trace a hull from a PNG alpha channel. The package builder can now write a deterministic `mesh_candidate_report.json` with `--report-mesh-candidates`, and can generate a draft `auto_mesh_plan.json` with `--auto-mesh-plan`. Those automatic plans are opt-in, conservative, first-pass proposals and remain review-required; a reviewed `--mesh-plan` always overrides the automatic draft path.

For autonomous-rigger research, `scripts/generate_rig_proposal.py` can produce a report-only `rig_proposal` that says which layers should remain regions and which are mesh candidates. That report is earlier than `--auto-mesh-plan`: it does not create topology, weights, or Spine output, and it must keep Chris-approved mesh fixtures and Spine Auto parity evidence as missing gates until real fixtures exist.

## Weights — binding bones to vertices

Weights let bones deform mesh vertices automatically when the bones move. The official guide's terminology table:

> Other names for allowing bones to affect mesh vertices include: linear blend skinning, blended skinning, multi-matrix skinning, skeletal subspace deformation, or sometimes simply "skinning". To avoid confusion with the unrelated **skins** feature in Spine, we use the name "weights".

A weight is a per-(vertex, bone) influence in [0, 1]. Per the docs, weights on a vertex always sum to 1.0 (the editor's adjustment tools enforce this). When `Auto` is clicked, Spine computes weights from mesh topography (not just distance to each bone) — the algorithm is "sophisticated" and good enough for most rigs as a starting point.

### The bind step

A mesh has no weights until bones are bound to it. Two paths:

1. Select the mesh, click `Bind`, then click each bone.
2. Select bones, click `Bind`, then click the mesh.

The editor computes auto-weights at bind time. From there, the `Weights` tool adjusts them per-vertex.

### Adjusting weights

- `Direct` mode — slider sets exact weight value for selected vertices.
- Brush modes — `Add` / `Remove` / `Replace` with size, strength, feather.
- `Smooth` averages a vertex's weights with its hull-edge neighbors. Useful to remove "I-set-this-vertex-to-100%-and-the-next-one-to-0%" hard creases.
- `Prune` removes weights below a threshold AND caps bones-per-vertex. The optimization step before shipping.

The docs are explicit that smoothing **increases vertex transforms** (more bones touching more vertices) and prune removes them. The right workflow: bind → auto → smooth where needed → prune for performance.

### Testing weights

The docs recommend creating a test animation that walks the bones through their maximum range, then adjusting weights with the animation playing in the preview view. When weighted meshes are emitted, the package builder now adds a review-only `__mesh_weight_test` animation that cycles bound bones through a small deterministic range so endpoint behavior, stretching, and silhouette drift can be inspected before animator cleanup.

Parity fixtures for autonomous-rigging claims must compare an approved Spine Editor export against plugin first-pass output on the same source mesh. Required checks include exact fixture vertex/triangle counts, approved bones-per-vertex budget, per-vertex weight sums within `0.001`, and a reviewed max per-influence weight delta. Until those fixtures pass, automatic weights remain first-pass review artifacts, not Spine Auto parity.

## Linked meshes — reuse without duplication

When the same mesh structure (vertices, edges, UVs, weights) needs to be used with different images, use a **linked mesh** instead of duplicating. The classic case: a flag mesh + different flag textures for different countries.

Linked meshes:

- Share vertices, edges, texture coordinates, weights with a source mesh.
- Can have their own image path (so the texture differs).
- If `Inherit timelines` is checked, deform keys from the source mesh apply to the linked mesh too.
- Must live under the same slot as the source mesh — or under skin placeholders in different skins, as long as the slot is the same.

JSON shape (verified from the official format doc):

```json
"slotName": {
  "myMesh": {
    "type": "linkedmesh",
    "path": "actualAttachmentName",
    "skin": "skinName",
    "parent": "sourceMeshName",
    "deform": true,
    "width": 121,
    "height": 132
  }
}
```

Slot-machine uses: variant skins for the same character (red king vs blue king), flag/banner reuse, repeated decorative elements across multiple JP tiers.

## Deform timelines — last resort

A deform timeline keys per-vertex offsets at specific times in an animation. The vertices move along straight lines between keys.

The official mesh doc is explicit: *"Most or all deformation should be done using weights. Using deform keys should be avoided or kept to a minimum."*

Why deform keys are a problem:

- They override the weight-driven deformation. If you key vertex N at time T to offset (5, 0), bone motion stops controlling that vertex during that key.
- Linear interpolation between deform keys means motion is straight-line — no curves, no acceleration, no follow-through.
- Each keyed vertex carries data in the JSON. A 100-vertex mesh with 30 keys = 3000 vertex offsets stored.

Valid uses:

- Subtle vertex-level cleanup of a weight-driven motion that can't be expressed by bone transforms alone (e.g., one pixel of perspective fix at a specific frame).
- A "secret" effect that can't be reached via weights (a face muscle twitching independently of bone motion).
- Linked-mesh inheritance for visual variants where only some frames differ.

For slot work, the skill **does not emit deform timelines**. If an effect genuinely requires per-vertex animation, that's an animator pass in Spine Editor, not pipeline code.

JSON shape of a deform timeline (verified from official format doc):

```json
"deform": {
  "skinName": {
    "slotName": {
      "meshName": [
        { "time": 0, "curve": [0.25, 0, 0.75, 1] },
        { "time": 1.5,
          "offset": 12,
          "vertices": [-0.756, -3.69, -1.02, -2.97, 0, 0, ...],
          "curve": [0.25, 0, 0.75, 1]
        }
      ]
    }
  }
}
```

`offset` is the number of vertex floats to skip before applying the `vertices` array; useful when only a slice of the mesh has nonzero deform.

## Mesh JSON contract

Region attachment converted to a mesh (this is what Spine Editor stores):

```json
"slot_name": {
  "attachment_name": {
    "type": "mesh",
    "path": "atlas_region_name",
    "uvs": [u0, v0, u1, v1, ...],
    "triangles": [t0a, t0b, t0c, t1a, t1b, t1c, ...],
    "vertices": [x0, y0, x1, y1, ...],
    "hull": 12,
    "edges": [...],
    "color": "ffffffff",
    "width": 108,
    "height": 143
  }
}
```

**Weighted mesh** — same fields, but `vertices` is interpreted differently:

> For each vertex either an x,y pair or, for a weighted mesh, first the number of bones which influence the vertex, then for that many bones: bone index, bind position X, bind position Y, weight. A mesh is weighted if the number of vertices > number of UVs.

(That last sentence is the key: the runtime decides "is this a weighted mesh" by comparing the count of vertices floats to twice the UV count. If `vertices.length > 2 * (uvs.length / 2)` then weighted.)

The skill emits unweighted mesh attachments from reviewed mesh plans by default. With `--auto-bind-weights`, the package builder can emit first-pass weighted vertices for reviewed plans or opt-in automatic draft plans, only when the plan or generated policy supplies explicit existing allowed bones. This uses topology-aware first-pass projection, endpoint locks, triangle-adjacency smoothing, and pruning. It is still not Spine Editor Auto parity, and the emitted `bindX`/`bindY` values are approximate local offsets for simple setup transforms.

Weighted mesh emission still needs:

1. A vertex layout (from the artist or an automatic tracer).
2. A bone-binding list (which bones can influence which vertices).
3. Either first-pass topology-aware weights or a hand-painted weight map.
4. Validation that hull and edges form a valid non-self-intersecting polygon.

## Performance reality

The official guide cites the vertex transform count and the fill-rate cost as the two primary mesh expenses. For slot games with ~30 symbols on screen at once:

- 30 symbols × 1 mesh each × 100 vertices × 2 bones-per-vertex = 6000 vertex transforms per frame just for mesh deformation.
- That's a soft budget on mid-range mobile, not a hard ceiling, but it argues strongly for "mesh only what visibly needs it."

A reasonable starting heuristic: never mesh more than one or two body parts per character HP symbol. Bodies that genuinely bend (a Santa whose belly squashes during HoHoHo, a snake that coils, a dragon whose tail swishes) earn the mesh. Heads, hats, accessories, and frame decorations stay regions.

## What's bundled, what isn't

| Capability | Status |
|---|---|
| Region attachments with the correct 4.x contract | Bundled (every slot emits a region by default) |
| Atlas with alpha-trimmed regions | Bundled (`build_atlas.py`) |
| Mesh attachment emission | Opt-in with reviewed `--mesh-plan`, or review-required automatic drafts via `--auto-mesh-plan` |
| Linked mesh emission | Not bundled — needs a source mesh in the project |
| First-pass weighted mesh binding | Opt-in with `--mesh-plan --auto-bind-weights` or `--auto-mesh-plan --auto-bind-weights`; explicit/generated existing allowed bones and animator review required |
| Final weight painting | Not bundled — needs an animator |
| Deform timeline emission | Not bundled (and discouraged by the docs anyway) |
| Mesh hull tracing | Bundled as `scripts/trace_mesh_hull.py`; automatic draft plans use conservative alpha bounds and still require review |

When a user asks the skill to "make this character squash on land," the honest answer is: the bundled pipeline gives them region-attachment scale animation (squash by `scale.x = 1.05, scale.y = 0.95`). For *real* squash where the head squishes wider while the chin pulls up, that's a mesh + weights pass in Spine Editor.
