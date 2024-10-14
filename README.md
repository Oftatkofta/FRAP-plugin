# Jens' ImageJ Plugins

A set of ImageJ plugins developed by Jens Eriksson.

Most plugins are written in Jython and can be copied to your FIJI/ImageJ plugins folder.

## Plugin Files

1. `Collective_Migration_buddy.py`: Analyzes collective cell migration with options for frame projection and time-lapse analysis of cell movement.

2. `Flatfield_normalizer.py`: Normalizes image flatfield by converting to float, normalizing based on maximum intensity, and converting back to 16-bit.

3. `FRAP_analysis_JE.py`: Performs Fluorescence Recovery After Photobleaching (FRAP) analysis with channel selection, automatic/manual post-bleach frame detection, and provides normalized FRAP curves and recovery parameters.

4. `PML_buddy.py`: A versatile plugin for tracking PML (Promyelocytic Leukemia) bodies and other dynamic cellular components in living cells. Features include:
   - Tracking PML body dynamics over time
   - Cropping around moving objects
   - Creating still "reference frames" around dynamic cell components
   - Analyzing various dynamic cellular structures

5. `Migration_buddy.py`: Analyzes migration of individual cells or cellular components, likely providing tools for tracking movement, measuring distances, and analyzing migration patterns or speeds.

## Usage

1. Copy the desired `.py` files to your FIJI/ImageJ plugins folder.
2. Restart FIJI/ImageJ or refresh the plugins folder.
3. Access the plugins from the Plugins menu in FIJI/ImageJ.
4. Follow on-screen instructions in the dialog boxes that appear.

## Installation

1. Ensure FIJI/ImageJ is installed on your system.
2. Locate your FIJI/ImageJ plugins folder (typically `[FIJI/ImageJ installation directory]/plugins/`).
3. Copy the `.py` files from this repository into the plugins folder.
4. Restart FIJI/ImageJ or use the "Refresh Menus" command to make the new plugins available.

## Requirements

These plugins require FIJI/ImageJ with Python support. Ensure you have the necessary dependencies installed, such as the `ij` module and its components (`WindowManager`, `IJ`, `ImagePlus`, etc.).

## TODO

- Implement proper documentation for each plugin
- Add example usage and sample results
- Create user guides for complex plugins
