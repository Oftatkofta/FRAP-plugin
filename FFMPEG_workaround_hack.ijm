// FFMPEG_ImageStack_to_MP4.ijm
// This script converts an image stack to an MP4 video using FFMPEG on Windows.
// It flattens overlays and preserves the current representation in the active window.

// FFMPEG Installation Instructions:
// 1. Download the latest FFMPEG build from https://ffmpeg.org/download.html
// 2. Extract the contents to C:\tools\ffmpeg-master-latest-win64-gpl
// 3. Add C:\tools\ffmpeg-master-latest-win64-gpl\bin to your system's PATH environment variable
// 4. Restart ImageJ/FIJI after modifying the PATH to ensure it recognizes the new FFMPEG installation

// Enable debug mode (set to true for verbose output)
debugMode = true;

// Function to print debug messages with timestamp
function debug(message) {
    if (debugMode) {
        getDateAndTime(year, month, dayOfWeek, dayOfMonth, hour, minute, second, msec);
        timestamp = "" + year + "-" + IJ.pad(month+1,2) + "-" + IJ.pad(dayOfMonth,2) + " " + IJ.pad(hour,2) + ":" + IJ.pad(minute,2) + ":" + IJ.pad(second,2);
        print(timestamp + " DEBUG: " + message);
    }
}

// Enable batch mode for faster processing
setBatchMode(true);
debug("Batch mode enabled");

// Set default FFMPEG folder and prompt the user
defaultFFMPEGFolder = "C:/tools/ffmpeg-master-latest-win64-gpl/bin/";
Dialog.create("FFMPEG Folder");
Dialog.addDirectory("Enter the path to ffmpeg folder:", defaultFFMPEGFolder);
Dialog.show();
ffmpegFolder = Dialog.getString();
ffmpegPath = ffmpegFolder + "ffmpeg.exe";
debug("FFMPEG path: " + ffmpegPath);

// Prompt the user for output directory
outputDirectory = getDirectory("Choose output directory:");
debug("Output directory: " + outputDirectory);

// Prompt the user for temporary frames directory
tempDirectory = getDirectory("Choose temporary frames directory:");
debug("Temporary directory: " + tempDirectory);

// Create a temporary directory to store frames if it doesn't already exist
if (!File.exists(tempDirectory)) {
    File.makeDirectory(tempDirectory);
    debug("Created temporary directory: " + tempDirectory);
}

// Prompt the user for frame rate
Dialog.create("Frame Rate");
Dialog.addNumber("Enter the frame rate:", 30);
Dialog.show();
frameRate = Dialog.getNumber();
debug("Frame rate: " + frameRate);

// Get the number of slices in the current image stack
stackSize = nSlices;
debug("Number of slices in stack: " + stackSize);

// Store original image ID and title
originalImageID = getImageID();
originalTitle = getTitle();
debug("Original image: " + originalTitle + " (ID: " + originalImageID + ")");

// Create a duplicate of the image/stack
run("Duplicate...", "duplicate");
debug("Image duplicated");

// Flatten the image/stack with overlays
run("Flatten", "stack");
debug("Image flattened");

// The flattened image is now the active one, so we can directly save it
run("Image Sequence... ", "format=PNG name=frame_ start=1 digits=4 save=[" + tempDirectory + "]");
debug("Saved " + stackSize + " flattened frames to " + tempDirectory);

// Close the flattened image/stack
close();
debug("Closed flattened image");

// If there's still an image open (the unflatted duplicate), close it
if (nImages > 1) {
    close();
    debug("Closed unflatted duplicate");
}

// Reselect the original image/stack
selectImage(originalImageID);
debug("Reselected original image");

// Get the title of the current image/stack (using the stored original title)
titleWithoutExtension = replace(originalTitle, ".tif", "");
outputFile = outputDirectory + titleWithoutExtension + ".mp4";
debug("Output file: " + outputFile);

// Build the FFMPEG command
ffmpegCommand = "\"" + ffmpegPath + "\" -framerate " + frameRate + 
    " -i \"" + tempDirectory + "frame_%04d.png\" -c:v libx264 -preset slow -crf 18 \"" + 
    outputFile + "\"";
debug("FFMPEG command: " + ffmpegCommand);

// Execute the FFMPEG command and capture the output
ffmpegOutput = exec("cmd", "/c", ffmpegCommand + " 2>&1");
debug("FFMPEG command executed. Output: " + ffmpegOutput);

// Check if the output file was created
if (File.exists(outputFile)) {
    debug("Output file created successfully: " + outputFile);
} else {
    debug("Error: Output file was not created. FFMPEG may have failed.");
    showMessage("Error", "Failed to create output file. Check the log for details.");
}

// Delete the temporary frame files
fileList = getFileList(tempDirectory);
deletedCount = 0;
for (i = 0; i < fileList.length; i++) {
    if (startsWith(fileList[i], "frame_") && endsWith(fileList[i], ".png")) {
        success = File.delete(tempDirectory + fileList[i]);
        if (success) {
            deletedCount++;
        } else {
            debug("Failed to delete file: " + tempDirectory + fileList[i]);
        }
    }
}
debug("Deleted " + deletedCount + " temporary frame files");

// Disable batch mode
setBatchMode(false);
debug("Batch mode disabled");

// Show completion message
if (File.exists(outputFile)) {
    showMessage("Video Creation Complete", "The video has been saved to:\n" + outputFile);
} else {
    showMessage("Error", "Failed to create the video. Check the log for details.");
}
debug("Script execution completed");

// Print final debug message to console
if (debugMode) {
    print("DEBUG: Script execution summary:");
    print("  - Input: " + originalTitle + " (" + stackSize + " frames)");
    print("  - Output: " + outputFile);
    print("  - Frame rate: " + frameRate + " fps");
    print("  - Temporary files created and deleted: " + deletedCount);
    print("  - FFMPEG output: " + ffmpegOutput);
}

// Ensure the script terminates
exit("Script finished. Check the log for details.");
