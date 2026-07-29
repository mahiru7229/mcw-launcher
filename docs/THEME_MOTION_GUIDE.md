# MCW Theme Motion Guide

MCW Launcher v0.11.0-alpha.4 introduces theme-driven interface motion through theme schema 4. Motion metadata never executes code; it only selects validated transition types, timings, easing curves, distances, and effect strengths.

## Manifest example

```json
{
  "schema_version": 4,
  "motion": {
    "page": {
      "type": "fade_slide",
      "duration_ms": 170,
      "easing": "out_cubic",
      "distance_px": 18
    },
    "button": {
      "hover_duration_ms": 100,
      "press_duration_ms": 70,
      "easing": "out_quad",
      "hover_strength": 0.08,
      "press_strength": 0.18
    },
    "dialog": {
      "type": "fade",
      "duration_ms": 160,
      "easing": "out_cubic"
    },
    "sidebar": {
      "duration_ms": 220,
      "easing": "out_cubic",
      "collapsed_width": 72
    },
    "launch_control": {
      "type": "fade",
      "duration_ms": 140,
      "easing": "out_cubic"
    }
  }
}
```

## Page transitions

Supported `page.type` values:

- `none`
- `fade`
- `slide_left`
- `slide_right`
- `fade_slide`

`distance_px` is limited to `0..256`. Page duration is limited to `0..3000 ms`.

## Dialog and Launch Control transitions

`dialog.type` and `launch_control.type` support `none` and `fade`. Dialogs fade when shown. Launch Control uses the configured transition when the Cancel control appears or disappears, and status badges pulse when their state changes.

## Button interaction

Button hover and press effects use a subtle color-strength animation so PNG and CSS themes keep their original shapes. `hover_strength` and `press_strength` use values from `0.0` to `1.0`; press strength cannot be lower than hover strength.

## Sidebar

The sidebar can collapse to icon-only navigation. `collapsed_width` is limited to `56..160 px`. Labels remain available as tooltips while collapsed.

## Easing values

- `linear`
- `in_quad`
- `out_quad`
- `in_out_quad`
- `in_cubic`
- `out_cubic`
- `in_out_cubic`
- `out_back`

## User motion modes

Launcher Settings provides three modes:

- **Full**: uses all theme motion values.
- **Reduced**: shortens durations and softens button effects.
- **Off**: changes state immediately without interface animation.

Theme authors do not need separate manifests for these modes. The launcher applies the user's accessibility preference at runtime.

## Compatibility and fallback

Themes using schema 1, 2, or 3 remain valid. A theme without `motion` receives the built-in safe motion defaults. Invalid motion metadata is ignored and reported as a theme issue; the launcher continues using defaults.
