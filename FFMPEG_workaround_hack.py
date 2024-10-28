# FFMPEG Installation on Windows:
# 1. Download the latest version of FFMPEG from https://ffmpeg.org/download.html#build-windows
# 2. Extract the downloaded ZIP file to a location of your choice (e.g., C:/tools/ffmpeg)
# 3. Add the bin folder within the extracted FFMPEG folder to your system's PATH environment variable
#    - Right-click on 'This PC' or 'My Computer' and select 'Properties'
#    - Click on 'Advanced system settings' and then 'Environment Variables'
#    - Under 'System Variables', find the 'Path' variable and click 'Edit'
#    - Add the path to the FFMPEG bin folder (e.g., C:/tools/ffmpeg/bin) and click 'OK'

# Running Jython Plugins in Fiji:
# 1. Download and install Fiji from https://fiji.sc/
# 2. Start Fiji and select 'Plugins' > 'Scripts' > 'New' > 'Script...'
# 3. Choose 'Python' as the language for the new script
# 4. Copy and paste this script into the script editor window
# 5. Save the script with a .py extension to the Fiji plugins folder or any subfolder
# 6. Run the script by selecting it from 'Plugins' > 'Scripts'

# User Inputs and Documentation:
# - debug_mode: Enable or disable debug mode for verbose output. Set to True or False.
# - ffmpeg_path: The path to the FFMPEG executable. Adjust according to your FFMPEG installation.
# - output_directory: The directory where the output video will be saved. This is chosen by the user at runtime.
# - frame_rate: The frame rate of the output video. Adjust as needed.
# - The script assumes the image stack is in RGB format. Ensure your image stack is RGB before running.

from ij import IJ, WindowManager
from ij.io import DirectoryChooser
from java.io import File
import os
import subprocess
import time

# Enable debug mode (set to True for verbose output)
debug_mode = True

# Function to print debug messages with timestamp
def debug(message):
    if debug_mode:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        IJ.log(timestamp + " DEBUG: " + message)

# Set default FFMPEG path (hardcoded)
ffmpeg_path = "C:/tools/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe"

# Verify that ffmpeg_path exists before proceeding
if not os.path.exists(ffmpeg_path):
    IJ.showMessage("Error", "FFMPEG executable not found at: " + ffmpeg_path + " Please verify the path and try again.")
    raise SystemExit("FFMPEG path verification failed.")
debug("FFMPEG path: " + ffmpeg_path)

# Prompt the user for output directory
output_directory = DirectoryChooser("Choose output directory").getDirectory()
if not output_directory:
    IJ.showMessage("Error", "No output directory selected.")
    raise SystemExit("No output directory selected.")
debug("Output directory: " + output_directory)

# Verify if an active image stack is present
if WindowManager.getImageCount() < 1:
    IJ.showMessage("Error", "No open images found.")
    raise SystemExit("No images found.")

# Get information about the current image
imp = IJ.getImage().duplicate()  # Work on a copy of the image stack to avoid renaming the original
original_title = imp.getTitle() + "_copy"
stack_size = imp.getStackSize()
debug("Original title: " + original_title)
debug("Number of slices in stack: " + str(stack_size))

# Assumption: The image stack is an RGB color stack
# The script assumes that each frame in the stack is a full-color (RGB) image.
# This is important because FFMPEG will expect the input frames to have color information
# when creating the video output. If the image stack is not RGB (e.g., grayscale or single-channel),
# the resulting video may not be correct, or FFMPEG may fail.
# Make sure that your input image stack is in RGB format before running this script.

# Set parameters for video generation
frame_rate = 24
output_filename = original_title + ".mp4"
output_file = os.path.join(output_directory, output_filename)
debug("Output file: " + output_file)

# Set temporary directory for frames
temp_directory = IJ.getDirectory("temp")
debug("Temporary directory for frames: " + temp_directory)

# Extract frames from the stack
if stack_size > 1:
    for i in range(1, stack_size + 1):
        imp.setSlice(i)
        frame_path = os.path.join(temp_directory, "frame_" + str(i).zfill(5) + ".png")
        IJ.saveAs(imp, "PNG", frame_path)
        debug("Saved frame: " + frame_path)    
else:
    IJ.showMessage("Error", "The current image is not a stack.")
    raise SystemExit("No stack available to convert.")

# Construct the FFMPEG command to convert image stack to MP4
ffmpeg_command = [
    ffmpeg_path,
    "-r", str(frame_rate),
    "-i", os.path.join(temp_directory, "frame_%05d.png"),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    output_file
]

# Execute the command and redirect output to a log file
temp_log_file = os.path.join(temp_directory, "ffmpeg_conversion_output.log")
with open(temp_log_file, "w") as log_file:
    process = subprocess.Popen(ffmpeg_command, stdout=log_file, stderr=subprocess.STDOUT)
    process.wait()

# Read and log the output of FFMPEG
with open(temp_log_file, "r") as log_file:
    ffmpeg_log = log_file.read()
    IJ.log("FFMPEG command output: " + ffmpeg_log)

# Notify the user that the command has been executed
IJ.log("FFMPEG conversion command executed: " + ' '.join(ffmpeg_command))

# Cleanup: Delete temporary frame files after FFMPEG completes
deleted_count = 0
for file_name in os.listdir(temp_directory):
    if file_name.startswith("frame_") and file_name.endswith(".png"):
        frame_path = os.path.join(temp_directory, file_name)
        try:
            os.remove(frame_path)
            deleted_count += 1
        except Exception as e:
            debug("Failed to delete file: " + frame_path + ", error: " + str(e))

debug("Deleted " + str(deleted_count) + " temporary frame files")

# Show a completion message to the user
if os.path.exists(output_file):
    IJ.showMessage("Video Creation Complete", "The video has been saved to: " + output_file)
else:
    IJ.showMessage("Error", "Failed to create the video. Check the log for details.")

debug("Script execution completed")

# Print final debug message to console
if debug_mode:
    IJ.log("DEBUG: Script execution summary:")
    IJ.log("  - Input: " + original_title + " (" + str(stack_size) + " frames)")
    IJ.log("  - Output: " + output_file)
    IJ.log("  - Frame rate: " + str(frame_rate) + " fps")
    IJ.log("  - Temporary files created and deleted: " + str(deleted_count))

IJ.log("Script finished. Check the log for details.")