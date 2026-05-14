# Profile README Context

- This repository is the special `ld000/ld000` profile README repository.
- The current visual direction is pixel game style.
- Dynamic profile assets are generated locally into `assets/` so the README stays readable even if third-party image services are slow.
- `scripts/update_pixel_profile.py` reads public GitHub data and writes SVG assets.
- `.github/workflows/update-pixel-profile.yml` runs the generator on a schedule and commits changed assets.
