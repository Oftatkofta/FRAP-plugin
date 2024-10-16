/*
How to Set Up FFMPEG on Windows

This guide will help you set up FFMPEG to work seamlessly on a Windows machine.

1. Install FFMPEG:
   - Go to https://ffmpeg.org/download.html and download the appropriate version for your system.
   - Extract the downloaded archive and add the `bin` directory to your system PATH for easy command-line access.

2. Verify the FFMPEG installation:
   - Open Command Prompt and run: `ffmpeg -version` to verify that FFMPEG is installed correctly.

3. Running Scripts with FFMPEG:
   - This script will use the installed version of FFMPEG to encode image stacks into a video.
*/

// Set default FFMPEG folder and prompt the user, allowing them to change if needed
defaultFFMPEGFolder = "C:/tools/ffmpeg-master-latest-win64-gpl/bin/";
Dialog.create("FFMPEG Folder");
Dialog.addDirectory("Enter the path to ffmpeg folder:", defaultFFMPEGFolder);
Dialog.show();
ffmpegFolder = Dialog.getString();
ffmpegPath = ffmpegFolder + "ffmpeg.exe";

// Prompt the user for output directory and generate output filename based on the active image stack
outputDirectory = getDirectory("Choose output directory:");
outputFile = outputDirectory + getTitle().replace('.png', '') + '.mp4';

// Prompt the user for temporary frames directory
tempDirectory = getDirectory("Choose temporary frames directory:");

// Prompt the user for framerate, default to the current playback framerate in ImageJ
frameRate = getNumber("Enter frame rate:", 30);  // Default to 30 fps if no playback framerate is available

// Create a temporary directory to store frames if it doesn't already exist
if (!File.exists(tempDirectory)) {
    File.makeDirectory(tempDirectory);
}

// Get the number of slices in the current image stack
stackSize = nSlices;

// List to keep track of created frame files
createdFiles = newArray();

// Loop through all slices and save each as a separate PNG image, with progress indication
for (i = 1; i <= stackSize; i++) {
    // Set the current slice to be saved
    setSlice(i);
    // Define the path for each frame to be saved in the temporary directory
    framePath = tempDirectory + "frame_" + i + ".png";
    // Save the current slice as a PNG image
    saveAs("PNG", framePath);
    // Add the created frame file to the list
    createdFiles[i - 1] = framePath;
    // Update progress
    showProgress(i, stackSize);
}

// Build the FFMPEG command to encode the saved frames into an MP4 video
ffmpegCommand = "\"" + ffmpegPath + "\" -framerate " + frameRate + 
    " -i \"" + tempDirectory + "frame_%d.png\" -c:v libx264 -preset slow -crf 18 \"" + 
    outputFile + "\"";

// Execute the FFMPEG command
exec(ffmpegCommand);

// Delete only the temporary frames that were created
for (i = 0; i < createdFiles.length; i++) {
    // Delete each individual frame that was created
    File.delete(createdFiles[i]);
}

// Notify the user that the process is complete
print("Video encoding complete: " + outputFile);
