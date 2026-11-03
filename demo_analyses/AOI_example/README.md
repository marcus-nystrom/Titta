# Map fixations to AOIs

`map_fixations_to_aois.py` maps each fixation to the area of interest (AOI) it falls in and writes the result to `fixation_aoi_hits.csv`. The fixations in `allfixations.txt` used in this example were extracted with the I2MC algorithm from raw data collected with the read_me.py demo (see `demo_experiment` folder). AOIs are black-and-white PNG images, one image per AOI.

This version processes **one trial (stimulus) at a time**. The AOI images of a trial are read from disk once. All fixations of all participants on that trial are then looked up in a single vectorized step. Trials can be processed in parallel.

## Requirements

- Python 3
- numpy, pandas, Pillow

```
pip install numpy pandas pillow
```

matplotlib is no longer needed.

## Input

### Fixation file (`allfixations.txt`)

A tab-separated file with one row per fixation. The script uses these columns:

| column        | meaning                                                            |
|---------------|--------------------------------------------------------------------|
| `participant` | participant id                                                     |
| `trial`       | stimulus file name; must match an AOI folder name, e.g. `im1.jpeg` |
| `xpos`, `ypos`| fixation position in pixels, origin at the top-left of the image   |
| `dur`         | fixation duration                                                  |

Other columns (as written by I2MC) are ignored. Fixations on trials without an AOI folder are skipped.

### AOI images (`AOIs/`)

- For each stimulus, create a folder with the same name as the stimulus file, e.g. `rabbits.jpg`. That folder holds the AOIs for that stimulus.
- Make each AOI as follows:
  1. Open the stimulus in Photoshop, GIMP, Inkscape, PowerPoint or even Paint.
  2. Make everything inside the AOI fully white and everything else fully black. An AOI can have any shape and can consist of several separate areas. Make sure areas in different AOIs do not overlap.
     A simple way to create AOIs is to draw them and export them as separate layers (PhotoCraft, Photoshop, GIMP, Inkscape).
  3. Save the file as **PNG** (not JPG).
  4. The file name is the AOI name. For example, the folder `rabbits.jpg` may contain `tail.png` and `ears.png`.
- The AOI image must have the same size as the screen/stimulus coordinates used for the fixations.

```
AOIs/
├── im1.jpeg/
│   ├── eye.png
│   └── tree.png
├── im2.jpeg/
│   └── bush.png
└── im3.jpeg/
    ├── house.png
    └── mountain.png
```

The example AOIs in the folder `AOIs` were drawn on the three images used in the read_me.py demo.

Only `.png` files are read, so files such as `Thumbs.db` or `.DS_Store` are ignored. For RGB(A) images only the red channel is used. A pixel belongs to the AOI if it has the maximum value of the image (white).

Turn off anti-aliasing when drawing AOIs. With the default setting, grey edge pixels (e.g. value 64 or 191 on rounded corners) are not exactly white, so they do not count as part of the AOI. To include them, set `AOI_THRESHOLD` (see Settings).

## Usage

Put the script next to `allfixations.txt` and the `AOIs` folder and run it from that folder:

```
python map_fixations_to_aois.py
```

### Settings (top of the script)

| setting         | default                   | meaning                                    |
|-----------------|---------------------------|--------------------------------------------|
| `FIXATION_FILE` | `'allfixations.txt'`      | fixation file                              |
| `AOI_FOLDER`    | `'AOIs'`                  | folder with one subfolder per stimulus     |
| `OUTPUT_FILE`   | `'fixation_aoi_hits.csv'` | output file                                |
| `N_WORKERS`     | `None`                    | number of trials processed in parallel     |
| `AOI_THRESHOLD` | `None`                    | which pixels count as AOI (see below)      |

`N_WORKERS`:

- `None` uses all CPU threads (`os.cpu_count()`).
- A number overrides this, e.g. `N_WORKERS = 16`.
- `N_WORKERS = 1` turns parallel processing off.

The script never uses more workers than there are trials. Memory use is roughly `N_WORKERS × (AOIs of one trial)`, plus about 70 MB per worker process for Python and its libraries (measured on Linux). Each AOI is stored as a boolean mask of 1 byte per pixel, about 2 MB for 1920×1080.

`AOI_THRESHOLD`:

- `None` counts only pixels with the maximum value of the image (pure white), as the old script did.
- A number from 0 to 255 counts every pixel brighter than that value, e.g. `AOI_THRESHOLD = 127`. Use `0` to count every non-black pixel. For 16-bit images the value is scaled automatically.

When running from **Spyder or Jupyter on Windows**, parallel processing may not work. Run the script from a terminal, or set `N_WORKERS = 1`.

### Console output (example)

```
Processing 400 trials with 28 worker(s)
1/400 im1.jpeg
...
123 fixations outside of screen. Counted as WS
Saved 412345 rows to fixation_aoi_hits.csv
Total time: 0 min 6.1 s
```

## Output (`fixation_aoi_hits.csv`)

| column            | meaning                                                           |
|-------------------|-------------------------------------------------------------------|
| `participant`     | participant id                                                    |
| `trial`           | stimulus name                                                     |
| `fixation_number` | fixation number within this participant and trial, starting at 1  |
| `xpos`, `ypos`    | fixation position                                                 |
| `dur`             | fixation duration                                                 |
| `AOI_name`        | name of the AOI hit, or `WS` (white space) if no AOI was hit      |

- Rows are in the same order as the fixation file.
- If AOIs overlap and a fixation falls in more than one AOI, the fixation gets one row per AOI hit, sorted by AOI name.
- Fixations outside the image, or with missing (NaN) coordinates, are `WS`.

## Performance

Measured on a real study with 400 trials, 5000+ AOIs and 400,000+ fixations (Intel Core i7-14700K, 64 GB RAM):

| version                                                                            | time                |
|------------------------------------------------------------------------------------|---------------------|
| old script, `many_aois = True`                                                     | ~12 hours           |
| old script, `many_aois = False`, split into 4 batches (each batch uses 25 GB RAM)  | ~1.5 hours in total |
| this script, `N_WORKERS = 1`                                                       | ~20 seconds         |
| this script, `N_WORKERS = 20` or `28`                                              | ~6 seconds          |

No batching is needed: only the AOIs of the trials being processed are kept in memory.

## Changes from the old script

The output format is unchanged. These behaviour changes are deliberate:

1. **Fixation numbers** restart for every participant + trial combination. The old script only restarted the count when the trial name changed.
2. **Negative coordinates** are `WS`. The old script used them as negative array indices, so they could hit an AOI on the opposite side of the image. Coordinates between −1 and 0 are now also outside the image (the old script counted them as pixel 0).
3. **Single-colour AOI images** (e.g. fully black) are ignored with a warning. In the old script every fixation hit such an AOI.
4. **Non-PNG files** in the AOI folders are ignored instead of crashing the script.
5. **Overlapping AOIs** are listed in alphabetical order instead of file system order.
6. Fixations outside the screen are reported once as a total instead of once per fixation per AOI.
