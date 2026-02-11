#include "PluginProcessor.h"

SimpleGainPlugin::SimpleGainPlugin()
    : AudioProcessor(BusesProperties()
        .withInput ("Input", juce::AudioChannelSet::stereo(), true)
        .withOutput("Output", juce::AudioChannelSet::stereo(), true))
{
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

    for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
    {
        auto* data = buffer.getWritePointer(channel);
        for (int i = 0; i < buffer.getNumSamples(); ++i)
            data[i] *= gain; // default: reduce volume by 50%
    }
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new SimpleGainPlugin();
}
