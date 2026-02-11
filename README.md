## SimpleGainPlugin

A super simple VST3 plugin with a fixed gain parameter. Built using CMake.

#### Features:
- Stereo input/output
- A gain variable, for gain processing.
- Demonstrates a simple plugin structure.

#### This project was created to learn:
- Simple JUCE audio processing architecture.
- CMake build system for VST3's

#### Build Instuctions:\
```bash
cd juce-SimpleGainPlugin/ # or where you have it cloned.
cmake -S . -B build
cmake --build build --congig Release
```
This repository assumes you have JUCE installed locally. Adjust JUCE_DIR in CMakeLists.txt to your local JUCE path.
