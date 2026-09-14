# Driver images

Rider photos imported from the MotoGP standings, normalised to a single asset spec:

| Property   | Value                                  |
|------------|----------------------------------------|
| Logical    | 36 x 26 pt                             |
| Density    | @3x                                    |
| Pixels     | **108 x 78**                           |
| Background | Solid white (`#FFFFFF`), no alpha      |
| Format     | PNG (RGB, optimized)                   |
| Naming     | `firstname_lastname.png`, lowercase ASCII |

Generate with:

    pip install pillow
    python3 scripts/import_driver_images.py

This folder is empty until that script is run somewhere with outbound network
access to `motorsport.com` — see the note in the repository README.
