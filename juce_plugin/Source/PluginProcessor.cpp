#include "PluginProcessor.h"

SimpleGainPlugin::SimpleGainPlugin()
    : AudioProcessor(BusesProperties()
        .withInput ("Input", juce::AudioChannelSet::stereo(), true)
        .withOutput("Output", juce::AudioChannelSet::stereo(), true))
{
    addParameter(gain = new juce::AudioParameterFloat("gain", "Gain", 0.0f, 1.0f, 1.0f));
    addParameter(bypass = new juce::AudioParameterBool("bypass", "Bypass", false));
}

void SimpleGainPlugin::prepareToPlay(double, int)
{
}

void SimpleGainPlugin::releaseResources()
{
}

void SimpleGainPlugin::processBlock(juce::AudioBuffer<float>& buffer,
                                    juce::MidiBuffer&)
{
    juce::ScopedNoDenormals noDenormals;

    if (bypass->get())
        return; // Input is already in the output buffer, so there is nothing to do.

    const float g = gain->get();

    for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
    {
        auto* data = buffer.getWritePointer(channel);
        for (int i = 0; i < buffer.getNumSamples(); ++i)
            data[i] *= g;
    }
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new SimpleGainPlugin();
}
