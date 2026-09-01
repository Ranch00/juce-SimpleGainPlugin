//------------------------------------------------------------------------
// Copyright(c) 2022 Steinberg Media Technologies GmbH.
//------------------------------------------------------------------------

#include "processor.h"
#include "cids.h"

#include "base/source/fstreamer.h"
#include "pluginterfaces/vst/ivstparameterchanges.h"

#include "public.sdk/source/vst/vstaudioprocessoralgo.h"

using namespace Steinberg;

namespace Steinberg {
//------------------------------------------------------------------------
// SimpleGainSDKProcessor
//------------------------------------------------------------------------
SimpleGainSDKProcessor::SimpleGainSDKProcessor ()
{
	//--- set the wanted controller for our processor
	setControllerClass (kSimpleGainSDKControllerUID);
}

//------------------------------------------------------------------------
SimpleGainSDKProcessor::~SimpleGainSDKProcessor ()
{}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKProcessor::initialize (FUnknown* context)
{
	// Here the Plug-in will be instantiated
	
	//---always initialize the parent-------
	tresult result = AudioEffect::initialize (context);
	// if everything Ok, continue
	if (result != kResultOk)
	{
		return result;
	}

	//--- create Audio IO ------
	addAudioInput (STR16 ("Stereo In"), Steinberg::Vst::SpeakerArr::kStereo);
	addAudioOutput (STR16 ("Stereo Out"), Steinberg::Vst::SpeakerArr::kStereo);

	return kResultOk;
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKProcessor::terminate ()
{
	// Here the Plug-in will be de-instantiated, last possibility to remove some memory!
	
	//---do not forget to call parent ------
	return AudioEffect::terminate ();
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKProcessor::setActive (TBool state)
{
	//--- called when the Plug-in is enable/disable (On/Off) -----
	return AudioEffect::setActive (state);
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKProcessor::process (Vst::ProcessData& data)
{
    //--- Read inputs parameter changes-----------
    if (data.inputParameterChanges)
    {
        int32 numParamsChanged = data.inputParameterChanges->getParameterCount ();
        for (int32 index = 0; index < numParamsChanged; index++)
        {
            Vst::IParamValueQueue* paramQueue =
                data.inputParameterChanges->getParameterData (index);
            if (paramQueue)
            {
                Vst::ParamValue value;
                int32 sampleOffset;
                int32 numPoints = paramQueue->getPointCount ();
                switch (paramQueue->getParameterId ())
                {
                    case SimpleGainSDKParams::kBypassId:
                        if (paramQueue->getPoint (numPoints - 1, sampleOffset, value) ==
                            kResultTrue)
                            mBypass = (value > 0.5f);
                        break;
                    case SimpleGainSDKParams::kParamGainId:
                        if (paramQueue->getPoint (numPoints - 1, sampleOffset, value) ==
                                kResultTrue)
                                mGain = value;
                        break;
                }
            }
        }
    }

    //--- Process Audio---------------------
    //--- ----------------------------------
    if (data.numInputs == 0 || data.numOutputs == 0)
    {
        // nothing to do
        return kResultOk;
    }

    int32 numChannels = data.inputs[0].numChannels;
    
    uint32 sampleFramesSize = getSampleFramesSizeInBytes(processSetup, data.numSamples);
    void** in = getChannelBuffersPointer (processSetup, data.inputs[0]);
    void** out = getChannelBuffersPointer (processSetup, data.outputs[0]);

    data.outputs[0].silenceFlags = 0;

    if (data.inputs[0].silenceFlags != 0)
    {
        // mark output silence too
        data.outputs[0].silenceFlags = data.inputs[0].silenceFlags;

        // the plug-in has to be sure that if it sets the flags silence that the output buffer are clear
        for (int32 i = 0; i < numChannels; i++)
        {
           // do not need to be cleared if the buffers are the same (in this case input buffer are
            // already cleared by the host)
            if (in[i] != out[i])
            {
                memset (out[i], 0, sampleFramesSize);
            }
        }
        // nothing to do at this point
        return kResultOk;
    }

    float gain = mGain;

    if (mBypass)
    {
        for (int32 i = 0; i < numChannels; i++)
        {
            int32 samples = data.numSamples;
            Vst::Sample32* ptrIn  = (Vst::Sample32*)in[i];
            Vst::Sample32* ptrOut = (Vst::Sample32*)out[i];
            while (--samples >= 0)
                *ptrOut++ = *ptrIn++;
        }
    }
    else
    {
        for (int32 i = 0; i < numChannels; i++)
        {
            int32 samples = data.numSamples;
            Vst::Sample32* ptrIn  = (Vst::Sample32*)in[i];
            Vst::Sample32* ptrOut = (Vst::Sample32*)out[i];
            while (--samples >= 0)
                *ptrOut++ = (*ptrIn++) * gain;
        }
    }
    return kResultOk;
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKProcessor::setupProcessing (Vst::ProcessSetup& newSetup)
{
	//--- called before any processing ----
	return AudioEffect::setupProcessing (newSetup);
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKProcessor::canProcessSampleSize (int32 symbolicSampleSize)
{
	// by default kSample32 is supported
	if (symbolicSampleSize == Vst::kSample32)
		return kResultTrue;

	// disable the following comment if your processing support kSample64
	/* if (symbolicSampleSize == Vst::kSample64)
		return kResultTrue; */

	return kResultFalse;
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKProcessor::setState (IBStream* state)
{
	if (!state)
		return kResultFalse;

	// called when we load a preset or project, the model has to be reloaded

	IBStreamer streamer (state, kLittleEndian);

	float savedParam1 = 0.f;
	if (streamer.readFloat (savedParam1) == false)
		return kResultFalse;

	int32 savedBypass = 0;
	if (streamer.readInt32 (savedBypass) == false)
		return kResultFalse;

	mGain = savedParam1;
	mBypass = savedBypass > 0;

	return kResultOk;
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKProcessor::getState (IBStream* state)
{
	// here we need to save the model (preset or project)

	float toSaveParam1 = mGain;
	int32 toSaveBypass = mBypass ? 1 : 0;

	IBStreamer streamer (state, kLittleEndian);
	streamer.writeFloat (toSaveParam1);
	streamer.writeInt32 (toSaveBypass);

	return kResultOk;
}





//------------------------------------------------------------------------
} // namespace Steinberg
