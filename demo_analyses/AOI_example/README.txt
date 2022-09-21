Run ´map_fixations_to_aois.py´ to map each fixation to an AOI (generates an output file ´fixation_aoi_hits.csv´). Fixations (allfixation.txt) used in this example were extracted with the I2MC algorithm from raw data collected with the read_me.py demo (see ´demos´ folder).

If you prefer Jypyter notebooks, see ´map_fixations_to_aois.ipynb´

How to make AOIs:
- For each stimulus, create a folder with the same name as the stimulus file, so e.g. "rabbits.jpg". In that folder, you will store the AOIs for that stimulus
- make them as follows:
1. open the file in photoshop, gimp, inkscape, or even paint
2. make everything that is inside the AOI fully white, everything else fully black. That means the AOI can have any shape, and also consist of multiple separate areas. Make sure that areas in different AOIs do not overlap.
   A simple way to create AOIs is to draw and export them as separate layers (photoshop, gimp, inkscape).
3. save this file as png (important, not jpg)
4. the name of the file is the name of the AOI. So e.g. the folder rabbits.jpg may contain tail.png and ears.png

The example AOIs in the folder ´AOIs´ were drawn on the three images used in the read_me.py demo. 
