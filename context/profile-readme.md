# Profile README Context

- This repository is the special `ld000/ld000` profile README repository.
- The current visual direction is Daily Stamp / Signal Passport.
- The README must avoid project introductions, specific project cards, project descriptions, and Selected Machines.
- Dynamic profile assets are generated locally into `assets/` so the README stays readable without third-party image services.
- Current assets are `assets/hero-signal-passport.png` and `assets/signal-panel.png`.
- `scripts/update_pixel_profile.py` reads public GitHub data and writes only those two PNG assets.
- The generated visuals use aggregate public data only: public repository count, total stars, top languages, and push pulse.
- `.github/workflows/update-pixel-profile.yml` runs the generator on a schedule and commits changed assets.
