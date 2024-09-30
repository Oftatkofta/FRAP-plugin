// ImageJ macro for segmenting DAPI nuclei in a specified channel, excluding edges,
// randomly selecting N ROIs, and measuring average fluorescence in specified measurement channels.

// Get the currently open image
originalImage = getTitle();

// Get the number of channels in the image
selectWindow(originalImage);
getDimensions(width, height, numChannels, numSlices, numFrames);

// Initialize arrays to hold measurement channel data
measurementChannels = newArray();
measurementChannelNames = newArray();

// Create the dialog
Dialog.create("Segmentation and Measurement Parameters");

// Segmentation parameters
Dialog.addNumber("Number of ROIs to select (N):", 10);
Dialog.addString("Size range for Analyze Particles (e.g., 50-Infinity):", "50-Infinity");
thresholdMethods = newArray("Default", "Huang", "Intermodes", "IsoData", "IJ_IsoData", "Li", "MaxEntropy", "Mean", "MinError(I)", "Minimum", "Moments", "Otsu", "Percentile", "RenyiEntropy", "Shanbhag", "Triangle", "Yen");
Dialog.addChoice("Thresholding method:", thresholdMethods, "Otsu");
Dialog.addNumber("DAPI channel number:", 1);
Dialog.addString("DAPI channel name (default: DAPI):", "DAPI");
Dialog.addCheckbox("Perform Watershed?", true);

// Measurement channels
Dialog.addMessage("Select measurement channels and provide custom names:");

for (i = 2; i <= numChannels; i++) {
    Dialog.addCheckbox("Measure in Channel " + i + "?", true);
    Dialog.addString("Channel " + i + " name (default: Channel " + i + "):", "Channel " + i);
}

Dialog.show();

// Retrieve segmentation parameters
N = Dialog.getNumber();
sizeRange = Dialog.getString();
thresholdMethod = Dialog.getChoice();
dapiChannel = parseInt(Dialog.getNumber());
dapiChannelName = Dialog.getString();
doWatershed = Dialog.getCheckbox();

// Retrieve measurement channel selections
measurementChannels = newArray();
measurementChannelNames = newArray();

for (i = 2; i <= numChannels; i++) {
    measureInChannel = Dialog.getCheckbox();
    channelName = Dialog.getString();
    if (measureInChannel) {
        if (i != dapiChannel) {
            measurementChannels = Array.concat(measurementChannels, i);
            if (channelName != "") {
                measurementChannelNames = Array.concat(measurementChannelNames, channelName);
            } else {
                measurementChannelNames = Array.concat(measurementChannelNames, "Channel " + i);
            }
        } else {
            // Warn the user if they attempted to select the DAPI channel as a measurement channel
            print("Warning: Channel " + i + " is the DAPI channel and will not be used as a measurement channel.");
        }
    }
}

// Check if at least one measurement channel is selected
if (measurementChannels.length == 0) {
    print("No measurement channels selected (excluding DAPI channel). Please select at least one channel to measure.");
    exit;
}

setBatchMode(true); // Run in batch mode to speed up processing
run("ROI Manager...");

// Duplicate the original image to work on
run("Duplicate...", "title=Working_Copy duplicate channels slices frames");

// Select the working image
selectWindow("Working_Copy");

// Ensure the image is in Hyperstack format
run("Stack to Hyperstack...", "order=xyczt(default) channels="+numChannels+" slices="+numSlices+" frames="+numFrames+" display=Color");

// Process the DAPI channel
Stack.setChannel(dapiChannel);

// Duplicate the DAPI channel
run("Duplicate...", "title=DAPI_Channel");

// Select the DAPI channel image
selectWindow("DAPI_Channel");

// Apply thresholding to segment nuclei
setAutoThreshold(thresholdMethod + " dark");

// Convert to mask
run("Convert to Mask");

// Optionally, perform watershed to separate touching nuclei
if (doWatershed) {
    run("Watershed");
}

// Analyze Particles to get ROIs, excluding edges
run("Analyze Particles...", "size=" + sizeRange + " exclude clear add");

// Now, ROIs are added to ROI Manager
roiCount = roiManager("count");

//print(roiCount);

if (roiCount == 0) {
    print("No ROIs found. Please check the segmentation parameters.");
    // Close all opened images except the original
    closeOpenedImagesExcept(originalImage);
    exit;
}

// Randomly select N ROIs from the ROI Manager
if (roiCount < N) {
    print("Warning: There are only " + roiCount + " ROIs. Selecting all of them.");
    N = roiCount;
}

// Generate a list of indices
roiIndices = newArray();
for (i = 0; i < roiCount; i++) {
    roiIndices[i] = i;
}

// Shuffle the indices using Fisher-Yates shuffle
for (i = roiCount - 1; i > 0; i--) {
    j = floor(random() * (i + 1));
    temp = roiIndices[i];
    roiIndices[i] = roiIndices[j];
    roiIndices[j] = temp;
}

// Select the first N indices
selectedIndices = newArray();
for (i = 0; i < N; i++) {
    selectedIndices[i] = roiIndices[i];
}
// **Disassociate ROIs from images**
roiManager("Associate", false);

// Remove unselected ROIs from the ROI Manager
removeUnselectedROIs(roiCount, selectedIndices);

// Clear results table
run("Clear Results");

// Set measurements to get mean intensity
run("Set Measurements...", "area mean standard redirect=None decimal=3");

// Select the Working_Copy image
selectWindow("Working_Copy");

// For each selected ROI, activate it and measure in each selected channel
for (i = 0; i < N; i++) {
    index = i; // After removing unselected ROIs, indices are from 0 to N-1
    
    // Initialize variables for this ROI
    roiLabel = "ROI_" + (i + 1);
    setResult("ROI", i, roiLabel);
    
    // For each measurement channel, measure and store results
    for (j = 0; j < measurementChannels.length; j++) {
        channelNum = measurementChannels[j];
        channelName = measurementChannelNames[j];
        
        // Set the channel
        Stack.setChannel(channelNum);
        
        // Select the ROI and ensure it is applied to the current image
        roiManager("Select", index);
        
        // Use getStatistics to get measurements without adding to the Results table
        getStatistics(area, mean, min, max, stdDev);
        
        // Store the measurements in the Results table
        setResult("Area_" + channelName, i, area);
        setResult("Mean_" + channelName, i, mean);
        setResult("StdDev_" + channelName, i, stdDev);
    }
}

// Close the working images
selectWindow("DAPI_Channel");
close();

selectWindow("Working_Copy");
close();

// Bring back the original image
selectWindow(originalImage);

// Results are in the Results table

setBatchMode(false);
print("Done.");

// Function to close all images except the specified one
function closeOpenedImagesExcept(exceptTitle) {
    allImages = getList("image.titles");
    for (k = 0; k < allImages.length; k++) {
        if (allImages[k] != exceptTitle) {
            selectWindow(allImages[k]);
            close();
        }
    }
}


// Function to remove unselected ROIs from the ROI Manager
function removeUnselectedROIs(totalROIs, selectedIndices) {
    // Create a lookup table for selected indices
    isSelected = newArray(totalROIs);
    for (i = 0; i < totalROIs; i++) {
        isSelected[i] = 0; // Initialize all to not selected
    }
    for (i = 0; i < selectedIndices.length; i++) {
        isSelected[selectedIndices[i]] = 1; // Mark selected ROIs
    }
    // Remove unselected ROIs starting from the end
    for (i = totalROIs - 1; i >= 0; i--) {
        if (isSelected[i] == 0) {
            roiManager("Select", i);
            roiManager("Delete");
        }
    }
}
