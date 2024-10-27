// FFMPEG_ImageStack_to_MP4.ijm
// This script converts an image stack to an MP4 video using FFMPEG on Windows.
// It assumes the image is already an RGB image and preserves the current representation in the active window.

// FFMPEG Installation Instructions:
// 1. Download the latest FFMPEG build from https://ffmpeg.org/download.html
// 2. Extract the contents to C:\tools\ffmpeg-master-latest-win64-gpl
// 3. Add C:\tools\ffmpeg-master-latest-win64-gpl\bin to your system's PATH environment variable
// 4. Restart ImageJ/FIJI after modifying the PATH to ensure it recognizes the new FFMPEG installation

// Enable debug mode (set to true for verbose output). Debug mode will provide detailed logging throughout the script to help diagnose issues.
debugMode = true;

// Function to print debug messages with timestamp
function debug(message) {
    if (debugMode) {
        getDateAndTime(year, month, dayOfWeek, dayOfMonth, hour, minute, second, msec);
        timestamp = "" + year + "-" + IJ.pad(month + 1, 2) + "-" + IJ.pad(dayOfMonth, 2) + " " + IJ.pad(hour, 2) + ":" + IJ.pad(minute, 2) + ":" + IJ.pad(second, 2);
        print(timestamp + " DEBUG: " + message);
    }
}

// Set default FFMPEG folder and prompt the user for its location
defaultFFMPEGFolder = "C:/tools/ffmpeg-master-latest-win64-gpl/bin/";
Dialog.create("FFMPEG Folder");
Dialog.addDirectory("Enter the path to ffmpeg folder:", defaultFFMPEGFolder);
Dialog.show();
ffmpegFolder = Dialog.getString();
ffmpegPath = ffmpegFolder + "ffmpeg.exe";

// Verify that ffmpegPath exists before proceeding
if (!File.exists(ffmpegPath)) {
    showMessage("Error", "FFMPEG executable not found at: " + ffmpegPath + "\nPlease verify the path and try again.");
    exit("FFMPEG path verification failed.");
}
debug("FFMPEG path: " + ffmpegPath); // Debug information for verifying FFMPEG path

// Prompt the user for output directory
outputDirectory = getDirectory("Choose output directory:");
debug("Output directory: " + outputDirectory); // Debug information for output directory

// Prompt the user for temporary frames directory
tempDirectory = getDirectory("Choose temporary frames directory:");
debug("Temporary directory: " + tempDirectory); // Debug information for temporary directory

// Create a temporary directory to store frames if it doesn't already exist
if (!File.exists(tempDirectory)) {
    File.makeDirectory(tempDirectory);
    debug("Temporary directory created: " + tempDirectory); // Debug information for directory creation
}

// Get current image stack information
imp = getTitle(); // Use getTitle() for the current image title in ImageJ macros
originalTitle = imp;
stackSize = nSlices;
frameRate = getNumber("Enter desired frame rate (fps):", 24);

// Enable batch mode only if processing multiple frames
if (stackSize > 1) {
    setBatchMode(true);
    debug("Batch mode enabled"); // Debug information for batch mode status
}

// Assume the image is already RGB and we know the dimensions
width = getWidth();
height = getHeight();
nChannels = 3; // Set the number of channels to 3, assuming RGB
slices = nSlices; // Correct usage to get image dimensions in ImageJ macro
debug("Image dimensions - Width: " + width + ", Height: " + height + ", Channels: " + nChannels + ", Slices: " + stackSize); // Debug information for image dimensions

// Prompt user to choose whether to duplicate the image stack
Dialog.create("Image Stack Duplication");
Dialog.addMessage("The image stack is large. Do you want to duplicate it to preserve the original?");
Dialog.addChoice("Duplicate Stack?", newArray("Yes", "No"), "Yes");
Dialog.show();
duplicateChoice = Dialog.getChoice();

if (duplicateChoice == "Yes") {
    run("Duplicate...", "title=TempStack"); // Duplicate the image stack without requiring further input
    newStack = getImageID();
    debug("Image stack duplicated.");
} else {
    newStack = getImageID(); // Use the existing stack without duplicating
    debug("Using original image stack without duplication.");
}

// Save each slice sequentially since parallel processing is not supported in ImageJ macro scripting.
// ImageJ's macro environment does not provide native support for multithreading, which means sequential processing is necessary.
// This ensures compatibility and avoids issues with simultaneous access to shared resources.
for (i = 1; i <= stackSize && i <= nSlices; i++) {
    if (duplicateChoice == "Yes") {
    selectImage(newStack);
} else {
    selectImage(newStack); // Select the image stack
}
    setSlice(i); // Set the current slice to be saved (ensure i is within bounds)
    framePath = tempDirectory + "frame_" + IJ.pad(i, 4) + ".png";
    saveAs("PNG", framePath); // Save the current slice as a PNG file
    debug("Saved frame: " + framePath); // Debug information for each saved frame
}

// Close the duplicated stack to free up memory if it was duplicated
if (duplicateChoice == "Yes") {
    selectImage(newStack); // Select the duplicated image by its ID
    close();
    debug("Duplicated stack closed to free up memory.");
}

// Construct the FFMPEG command to create the video
// The -preset slow parameter is used to optimize compression efficiency, resulting in better quality at the cost of slower processing time.
// The -crf 18 parameter sets the quality level for the output video; lower values mean better quality (18 is generally considered visually lossless).
Dialog.create("Output File Name");
Dialog.addString("Enter the desired output filename (without extension):", originalTitle);
Dialog.show();
outputFilename = Dialog.getString();
outputFile = outputDirectory + outputFilename + ".mp4";
ffmpegCommand = "\"" + ffmpegPath + "\" -y -framerate " + frameRate + 
    " -i \"" + tempDirectory + "frame_%04d.png\" -c:v libx264 -preset slow -crf 18 \"" + 
    outputFile + "\"";
debug("FFMPEG command: " + ffmpegCommand); // Debug information for FFMPEG command construction

// Execute the FFMPEG command and capture the return code
tempLogFile = tempDirectory + "ffmpeg_output.log";
exec("cmd /c " + ffmpegCommand + " > " + tempLogFile + " 2>&1");
ffmpegReturnCode = File.exists(outputFile) ? 0 : 1;
if (ffmpegReturnCode != 0) {
    // Log the FFMPEG output for debugging
    ffmpegLog = File.openAsString(tempLogFile);
    debug("FFMPEG command failed. Log output:
" + ffmpegLog);
}
if (ffmpegReturnCode != 0) {
    // If the return code is non-zero, log the error and exit
    debug("Error: FFMPEG command failed with return code " + ffmpegReturnCode); // Debug information for command failure
    showMessage("Error", "FFMPEG command failed. Check the log for details.");
    exit("FFMPEG execution failed.");
} else {
    debug("FFMPEG command executed successfully."); // Debug information for successful command execution
}

// Verify if the output video file was created
if (File.exists(outputFile)) {
    debug("Output file created successfully: " + outputFile); // Debug information for successful file creation
} else {
    debug("Error: Output file was not created. FFMPEG may have failed.");
    showMessage("Error", "Failed to create output file. Check the log for details.");
}

// Delete the temporary frame files to clean up
fileList = getFileList(tempDirectory);
deletedCount = 0;
for (i = 0; i < fileList.length; i++) {
    if (startsWith(fileList[i], "frame_") && endsWith(fileList[i], ".png")) {
        success = false;
        retries = 3;
        while (retries > 0 && !success) {
            success = File.delete(tempDirectory + fileList[i]);
            if (success) {
                deletedCount++;
            } else {
                debug("Failed to delete file: " + tempDirectory + fileList[i] + ", retries left: " + (retries - 1)); // Debug information for failed deletion
                wait(500); // Wait for 500ms before retrying to delete the file
                retries--;
            }
        }
        if (!success) {
            debug("Failed to delete file after retries: " + tempDirectory + fileList[i]); // Debug information for final failed deletion
        }
    }
}
debug("Deleted " + deletedCount + " temporary frame files"); // Debug information for cleanup status

// Disable batch mode if it was enabled earlier
if (stackSize > 1) {
    setBatchMode(false);
    debug("Batch mode disabled"); // Debug information for disabling batch mode
}

// Show a completion message to the user
if (File.exists(outputFile)) {
    showMessage("Video Creation Complete", "The video has been saved to:\n" + outputFile);
} else {
    showMessage("Error", "Failed to create the video. Check the log for details.");
}
debug("Script execution completed"); // Final debug message

// Print final debug message to console
if (debugMode) {
    print("DEBUG: Script execution summary:");
    print("  - Input: " + originalTitle + " (" + stackSize + " frames)");
    print("  - Output: " + outputFile);
    print("  - Frame rate: " + frameRate + " fps");
    print("  - Temporary files created and deleted: " + deletedCount);
    print("  - FFMPEG return code: " + ffmpegReturnCode);
}

// Ensure the script terminates with a message
exit("Script finished. Check the log for details.");
