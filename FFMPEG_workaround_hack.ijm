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
    debug("Temporary directory created: " + tempDirectory);
}

// Get current image stack information
originalTitle = getTitle();
stackSize = nSlices;
frameRate = getNumber("Enter desired frame rate (fps):", 24);

// Enable batch mode only if processing multiple frames
if (stackSize > 1) {
    setBatchMode(true);
    debug("Batch mode enabled");
}

// Get dimensions of the current image
getDimensions(width, height, nChannels, nSlices);
debug("Image dimensions - Width: " + width + ", Height: " + height + ", Channels: " + nChannels + ", Slices: " + stackSize);

// Duplicate the image stack to avoid modifying the original
run("Duplicate...", "title=TempStack duplicate");
newStack = getImageID();

// Create a thread pool to save each slice in parallel for improved performance
stackExecutor = new java.util.concurrent.Executors.newFixedThreadPool(java.lang.Runtime.getRuntime().availableProcessors());
for (i = 1; i <= stackSize; i++) {
    final sliceIndex = i;
    stackExecutor.submit(new Runnable() {
        run() {
            setSlice(sliceIndex); // Set the current slice to be saved
            run("Flatten"); // Flatten to ensure overlays are preserved in the saved image
            framePath = tempDirectory + "frame_" + IJ.pad(sliceIndex, 4) + ".png";
            saveAs("PNG", framePath); // Save the current slice as a PNG file
            debug("Saved frame: " + framePath);
        }
    });
}
stackExecutor.shutdown();
while (!stackExecutor.isTerminated()) {
    wait(100); // Wait for all threads to complete
}

// Close the duplicated stack to free up memory
selectWindow("TempStack");
close();

// Construct the FFMPEG command to create the video
outputFile = outputDirectory + originalTitle + ".mp4";
ffmpegCommand = "\"" + ffmpegPath + "\" -y -framerate " + frameRate + 
    " -i \"" + tempDirectory + "frame_%04d.png\" -c:v libx264 -preset slow -crf 18 \"" + 
    outputFile + "\"";
debug("FFMPEG command: " + ffmpegCommand);

// Execute the FFMPEG command and capture the return code
ffmpegReturnCode = System.exec("cmd /c " + ffmpegCommand);
if (ffmpegReturnCode != 0) {
    // If the return code is non-zero, log the error and exit
    debug("Error: FFMPEG command failed with return code " + ffmpegReturnCode);
    showMessage("Error", "FFMPEG command failed. Check the log for details.");
    exit("FFMPEG execution failed.");
} else {
    debug("FFMPEG command executed successfully.");
}

// Verify if the output video file was created
if (File.exists(outputFile)) {
    debug("Output file created successfully: " + outputFile);
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
                debug("Failed to delete file: " + tempDirectory + fileList[i] + ", retries left: " + (retries - 1));
                wait(500); // Wait for 500ms before retrying to delete the file
                retries--;
            }
        }
        if (!success) {
            debug("Failed to delete file after retries: " + tempDirectory + fileList[i]);
        }
    }
}
debug("Deleted " + deletedCount + " temporary frame files");

// Disable batch mode if it was enabled earlier
if (stackSize > 1) {
    setBatchMode(false);
    debug("Batch mode disabled");
}

// Show a completion message to the user
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
    print("  - FFMPEG return code: " + ffmpegReturnCode);
}

// Ensure the script terminates with a message
exit("Script finished. Check the log for details.");
