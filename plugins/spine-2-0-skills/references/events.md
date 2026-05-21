# Events

Events are named timeline triggers — the game code listens for them and decides what to do. The Spine runtime delivers events to your listener when an animation reaches their timestamp; the runtime itself takes no action. This file covers when to use events in slot animation, the JSON contract, and the skill's emission rules.

Verified against the official Spine events documentation and the runtime Applying Animations guide.

## What an event is — and isn't

> An event is a trigger for something to happen during an animation. In the Spine editor, an event can be configured to play audio. Otherwise, events are intended to be handled at runtime, where you can write code to take whatever action you like in response to the events.

Events are **named timeline points**. They have:

- A unique name per skeleton (e.g. `win/jackpot_reveal`).
- Optional int, float, and string payloads with defaults set at the skeleton level, overridable per-key.
- Optional audio path, volume, and balance for editor playback only — the runtime does NOT play audio automatically.

The runtime contract (verified against the Applying Animations doc):

- `AnimationState.update(delta)` advances time and queues events between `lastTime` and the new time.
- `AnimationState.apply(skeleton)` invokes listeners with the queued events.
- Multiple events can fire in one frame; listeners are called in timeline order.
- An EventTimeline fires every event whose time is in `(lastTime, time]` — strictly greater than the previous frame's time, less than or equal to the new time.

Game-side responsibilities:

- **Audio playback** — the listener uses the event's `audio` / `volume` / `balance` properties and dispatches to whatever audio engine the game uses. The Spine runtime ships zero audio code.
- **Particle / VFX spawning** — the listener spawns a particle system at the listener's chosen location.
- **Math / state updates** — the listener tells the math engine "scatter landed," tells the credit counter "start jackpot reveal," tells the bonus system "trigger feature."

The skill never claims to *handle* events. It emits the data in the JSON so the game's listener has something to listen to.

## When to add events in slot animation

Three rules from the slot-machine context:

1. **Game state changes** — any visual moment that the game logic also needs to know about. Bonus triggers, scatter lands, jackpot reveals, free-spin entry/exit, big-win threshold crossings, feature activations.
2. **Audio sync** — any sound that should be tightly coupled to a visual beat. A coin clink at the moment the coin hits the meter, a Ho-Ho-Ho beat aligned with a mouth swap, a glass shatter on a winframe explode.
3. **Cross-system handoffs** — moments where two production systems (math, audio, UI, presentation) need to agree on timing. Free-spin transitions are the canonical case: a `transition/free_spins_in` event fires at the apex of the intro animation, which tells the presentation layer to switch backgrounds and tells the math layer to start the free-spin count.

Events are **not** for purely visual effects. A glow that fades in and out is a slot color keyframe, not an event. A particle that spawns from a sparkle is — in slot architecture — usually still a slot color / attachment swap because the particle system is in-engine. Events earn complexity when the audience for the trigger is more than just the renderer.

## Naming conventions

The official guide notes that editor folders become slash-prefixed prefixes on event names:

> In exported skeleton data, folder names are prepended to the event name to create the final name used in the Spine Runtimes. For example, if the folder `attacks` has an event `reload`, then the event name at runtime is `attacks/reload`.

The slot-machine convention this skill recommends:

```
win/<symbol_role>_<beat>      e.g.  win/hp_reveal, win/jp_grand_reveal
scatter/land                   single scatter landing
scatter/count_<n>              when n-th scatter lands, for the trigger logic
bonus/trigger                  bonus mode entry
bonus/end                      bonus mode exit
feature/start                  feature mode entry
feature/end                    feature mode exit
transition/free_spins_in       free-spin transition apex
transition/free_spins_out      free-spin exit apex
audio/<symbol>_<beat>          audio-only beats (Ho-Ho-Ho, coin clink)
jackpot/tier_<n>_reveal        jackpot tier reveal beat
meter/state_<n>_collect        meter advances to state N
```

These are conventions, not contract. The game team owns the actual event naming scheme — the skill respects whatever the user supplies.

## Event JSON contract

Verified field-by-field against the official format documentation.

### Top-level event definition (under `"events"` in the skeleton JSON)

```json
"events": {
  "win/hp_reveal": {
    "int": 0,
    "float": 0,
    "string": "",
    "audio": "win/hp_reveal.wav",
    "volume": 1.0,
    "balance": 0.0
  },
  "scatter/land": {
    "int": 0
  }
}
```

Field rules:

- `int` — whole number, default 0.
- `float` — number with optional fraction, default 0.
- `string` — text payload, default null.
- `audio` — path to audio file for editor playback (the runtime does NOT play this automatically), default null.
- `volume` — 0.0–1.0, default 1.0. Editor playback only.
- `balance` — -1.0 (left) to 1.0 (right), default 0.0. Editor playback only.

### Per-animation event timeline (under animation's `"events"`)

```json
"events": [
  { "time": 0.36, "name": "audio/santa_hoho_beat_1" },
  { "time": 0.92, "name": "audio/santa_hoho_beat_2" },
  { "time": 1.48, "name": "audio/santa_hoho_beat_3", "int": 3 },
  { "time": 1.85, "name": "win/hp_reveal", "string": "rank=3" }
]
```

Per-key fields:

- `time` — required, seconds.
- `name` — required, must reference a top-level event definition.
- `int`, `float`, `string` — override the setup values; if omitted, the setup values apply.
- `volume`, `balance` — override editor-playback values.

### Runtime listener pattern (game code, not skill code)

The Applying Animations doc shows the canonical pattern:

```
AnimationState state = ...;
state.addListener(new AnimationStateAdapter() {
  @Override
  public void event(TrackEntry entry, Event event) {
    String name = event.getData().getName();
    int intValue = event.getInt();
    float floatValue = event.getFloat();
    String stringValue = event.getString();
    String audioPath = event.getData().getAudioPath();
    float volume = event.getVolume();
    float balance = event.getBalance();
    // Dispatch by name to the right game system.
  }
});
```

The skill cannot write this; it's the game team's runtime integration. What the skill can do is document which events its emission expects to fire, so the integration team knows what to listen for.

## The skill's event emission

Default: **no events emitted**. The portable pipeline produces animations without events.

`--enable-events <events_plan.json>`: the user supplies a plan describing which events fire on which animations at which times. Plan shape:

```json
{
  "events": {
    "win/hp_reveal": {"audio": "win/hp_reveal.wav"},
    "audio/hoho_beat": {"audio": "audio/hoho_beat.wav"}
  },
  "animations": {
    "HP3win": [
      { "time": 0.36, "name": "audio/hoho_beat", "int": 1 },
      { "time": 0.92, "name": "audio/hoho_beat", "int": 2 },
      { "time": 1.48, "name": "audio/hoho_beat", "int": 3 },
      { "time": 1.85, "name": "win/hp_reveal" }
    ],
    "HP3land": [
      { "time": 0.05, "name": "audio/land_thud" }
    ]
  }
}
```

The skill:

1. Adds top-level event definitions to the skeleton.
2. Splices the per-animation event timelines into the matching animation.
3. Validates that every animation referenced in the plan exists in the rig.
4. Validates that every event referenced in the timelines is defined at the top level.

The strict 4.x compatibility checks accept events as defined. The skill's emission passes.

## Audio events vs game-state events

Two flavors:

**Audio events** — have an `audio` path. The Spine editor previews them at authoring time. The runtime listener's responsibility is to play the audio file. The audio path is relative to the game's audio root, conventionally something like `sfx/` or `audio/`.

**Game-state events** — no audio path, or the audio path is set but the listener ignores it. Pure game-logic triggers. The math engine cares; the audio system might or might not.

In slot work, both kinds are common. Audio events for sub-second-precision sound timing (coin clink, mouth pop, glass shatter). Game-state events for math / system triggers (scatter count, jackpot tier reveal, bonus trigger).

## Common patterns

### Ho-Ho-Ho character beats

```json
"HP3win": {
  ...
  "events": [
    { "time": 0.36, "name": "audio/hoho_beat_1" },
    { "time": 0.92, "name": "audio/hoho_beat_2" },
    { "time": 1.48, "name": "audio/hoho_beat_3" }
  ]
}
```

Each beat aligns with a mouth-swap stepped attachment timeline. The audio listener triggers the "Ho" sound; the visual is driven by the slot attachment timeline.

### Scatter trigger countdown

```json
"SC1land": {
  ...
  "events": [
    { "time": 0.05, "name": "audio/scatter_land" },
    { "time": 0.2, "name": "scatter/land", "int": 1 }
  ]
}
```

The math engine counts scatter lands; the third scatter triggers the bonus mode, which is the game code's decision based on the cumulative `scatter/land` events.

### Free-spin transition

```json
"FB_Transition": {
  ...
  "events": [
    { "time": 0, "name": "transition/free_spins_in" },
    { "time": 0.8, "name": "audio/transition_swoosh" },
    { "time": 1.5, "name": "transition/free_spins_in_complete" }
  ]
}
```

Game code listens for `transition/free_spins_in` to start prepping the free-spin scene, for `transition/free_spins_in_complete` to actually switch state.

### Jackpot tier reveal

```json
"JP1win": {
  ...
  "events": [
    { "time": 0.3, "name": "audio/jp_grand_buildup" },
    { "time": 1.2, "name": "audio/jp_grand_hit" },
    { "time": 1.2, "name": "jackpot/tier_1_reveal", "int": 1, "string": "GRAND" }
  ]
}
```

Two events at the same time — both fire in the same frame. Audio listener plays the hit, game listener starts the credit counter.

## What the skill cannot do

- **Author the event plan.** Which events fire when is a creative + game-logic decision. The skill can suggest event slots from the family's animation set (the four standard beats), but the user supplies the plan.
- **Wire up listeners.** Listener code lives in the game runtime, not in Spine data.
- **Play audio.** Audio playback is the listener's responsibility; the runtime ships no audio code.
- **Guarantee event ordering across multiple tracks.** If a game plays two animations on different tracks and both fire events at the same time, listeners get both — ordering is by timeline order within the track, but cross-track interleaving is the game's concern.

## Validation

The strict 4.x compatibility checks don't enforce event semantics (they are format-shape checks), but the skill's own assembler validates:

- Top-level event names match the regex `[a-zA-Z0-9_/-]+` (the slash for editor folder paths).
- Per-animation event timeline times are non-negative and within the animation's duration.
- Every referenced event name has a top-level definition.
- No event timeline appears in more than one animation under the same time (warning, not error — the runtime allows it, but it's almost always a mistake).
