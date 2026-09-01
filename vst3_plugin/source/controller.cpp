//------------------------------------------------------------------------
// Copyright(c) 2022 Steinberg Media Technologies GmbH.
//------------------------------------------------------------------------

#include "controller.h"
#include "cids.h"
#include "base/source/fstreamer.h"
#include "pluginterfaces/base/ibstream.h"

using namespace Steinberg;

namespace Steinberg {

//------------------------------------------------------------------------
// SimpleGainSDKController Implementation
//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKController::initialize (FUnknown* context)
{
	// Here the Plug-in will be instantiated

	//---do not forget to call parent ------
	tresult result = EditControllerEx1::initialize (context);
	if (result != kResultOk)
	{
		return result;
	}

	// Here you could register some parameters
	if (result == kResultTrue)
	{
		//---Create Parameters------------
        parameters.addParameter (STR16 ("Gain"), STR16 ("dB"), 0, 1.0, Vst::ParameterInfo::kCanAutomate,
                                 SimpleGainSDKParams::kParamGainId, 0);

		parameters.addParameter (STR16 ("Bypass"), nullptr, 1, 0,
		                         Vst::ParameterInfo::kCanAutomate | Vst::ParameterInfo::kIsBypass,
		                         SimpleGainSDKParams::kBypassId);
	}

	return result;
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKController::terminate ()
{
	// Here the Plug-in will be de-instantiated, last possibility to remove some memory!

	//---do not forget to call parent ------
	return EditControllerEx1::terminate ();
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKController::setComponentState (IBStream* state)
{
	// Here you get the state of the component (Processor part)
	if (!state)
		return kResultFalse;

	IBStreamer streamer (state, kLittleEndian);

	float savedParam1 = 0.f;
	if (streamer.readFloat (savedParam1) == false)
		return kResultFalse;
	setParamNormalized (SimpleGainSDKParams::kParamGainId, savedParam1);


	// read the bypass
	int32 bypassState;
	if (streamer.readInt32 (bypassState) == false)
		return kResultFalse;
	setParamNormalized (kBypassId, bypassState ? 1 : 0);

    // sync with our parameter
    if (auto param = parameters.getParameter (SimpleGainSDKParams::kParamGainId))
        param->setNormalized (savedParam1);

	return kResultOk;
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKController::setState (IBStream* state)
{
	// Here you get the state of the controller

	return kResultTrue;
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKController::getState (IBStream* state)
{
	// Here you are asked to deliver the state of the controller (if needed)
	// Note: the real state of your plug-in is saved in the processor

	return kResultTrue;
}

//------------------------------------------------------------------------
IPlugView* PLUGIN_API SimpleGainSDKController::createView (FIDString name)
{
	return nullptr;
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKController::setParamNormalized (Vst::ParamID tag, Vst::ParamValue value)
{
	// called by host to update your parameters
	tresult result = EditControllerEx1::setParamNormalized (tag, value);
	return result;
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKController::getParamStringByValue (Vst::ParamID tag, Vst::ParamValue valueNormalized, Vst::String128 string)
{
	// called by host to get a string for given normalized value of a specific parameter
	// (without having to set the value!)
	return EditControllerEx1::getParamStringByValue (tag, valueNormalized, string);
}

//------------------------------------------------------------------------
tresult PLUGIN_API SimpleGainSDKController::getParamValueByString (Vst::ParamID tag, Vst::TChar* string, Vst::ParamValue& valueNormalized)
{
	// called by host to get a normalized value from a string representation of a specific parameter
	// (without having to set the value!)
	return EditControllerEx1::getParamValueByString (tag, string, valueNormalized);
}

//------------------------------------------------------------------------
} // namespace Steinberg
