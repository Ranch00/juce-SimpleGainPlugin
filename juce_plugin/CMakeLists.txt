cmake_minimum_required(VERSION 3.22)

project(SGP VERSION 0.0.1)

# Path to JUCE (adjust if needed)
set(JUCE_DIR /home/rrancans/dev/audio/juce)

add_subdirectory(${JUCE_DIR} JUCE)


juce_add_plugin(SimpleGainPlugin
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    COPY_PLUGIN_AFTER_BUILD TRUE
    PLUGIN_MANUFACTURER_CODE Juce
    PLUGIN_CODE Sgpl
    FORMATS VST3
    PRODUCT_NAME "SimpleGainPlugin"
)

# juce_generate_juce_header(SimpleGainPlugin)

target_sources(SimpleGainPlugin
    PRIVATE
        Source/PluginProcessor.cpp
        Source/PluginProcessor.h
)

target_compile_definitions(SimpleGainPlugin
    PUBLIC
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
        JUCE_VST3_CAN_REPLACE_VST2=0
)

target_link_libraries(SimpleGainPlugin
    PRIVATE
        juce::juce_audio_utils
        juce::juce_audio_processors
)
