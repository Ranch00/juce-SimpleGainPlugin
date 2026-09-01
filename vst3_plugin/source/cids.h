//------------------------------------------------------------------------
// Copyright(c) 2022 Steinberg Media Technologies GmbH.
//------------------------------------------------------------------------

#pragma once

#include "pluginterfaces/base/funknown.h"
#include "pluginterfaces/vst/vsttypes.h"

namespace Steinberg {

//------------------------------------------------------------------------
enum SimpleGainSDKParams : Vst::ParamID
{
	kBypassId = 100,
    kParamGainId = 101,
};

//------------------------------------------------------------------------
static const Steinberg::FUID kSimpleGainSDKProcessorUID (0x32CDAFC3, 0x34DF5CB4, 0xAB1C312D, 0xB1525368);
static const Steinberg::FUID kSimpleGainSDKControllerUID (0xA235FD83, 0xDAFC59DF, 0x53258E2F, 0xB1C3235B);

#define SimpleGainSDKVST3Category "Fx"

//------------------------------------------------------------------------
} // namespace Steinberg
