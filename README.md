# FRAP-plugin
A set of ImageJ plugins developed by Jens Eriksson at Nanoscopy Gaustad, a node in the Core facility for advanced light microscopy at Oslo university Hospital.

All plugins are written in python and the files can be copied to your FIJI/ImageJ plugins-folder.

## Plugin Files

Here's a list of the plugin files included in this repository:

1. `Collective_Migration_buddy.py`: A plugin for analyzing collective cell migration. It provides options for frame projection and time-lapse analysis of cell movement.

2. `Flatfield_normalizer.py`: A simple plugin that normalizes the flatfield of an image. It converts the image to float, normalizes it based on the maximum intensity, and then converts it back to a 16-bit image.

3. `FRAP_analysis_JE.py`: A plugin for Fluorescence Recovery After Photobleaching (FRAP) analysis. It allows for channel selection, automatic or manual post-bleach frame detection, and provides normalized FRAP curves and recovery parameters.

4. `PML_buddy.py`: A versatile plugin primarily designed to track PML (Promyelocytic Leukemia) bodies in living cells. It offers additional functionalities:
   - Tracks PML body dynamics and behavior over time in cellular imaging experiments.
   - Can crop around moving objects, allowing for focused analysis of specific cellular components.
   - Creates a still "reference frame" around dynamic cell components, facilitating the study of relative movements and changes.
   - Can be used to track and analyze various dynamic cellular structures beyond PML bodies.

5. `Migration_buddy.py`: A plugin designed to analyze the migration of individual cells or cellular components. It provides tools for tracking movement, measuring distances, and analyzing migration patterns or speeds.

#TODO Proper documentation (I promise...maybe...) 
