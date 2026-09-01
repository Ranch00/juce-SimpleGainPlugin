For my senior project at University College Roosevelt, I wanted to answer a fairly simple question:

**Does JUCE add measurable CPU overhead compared with implementing the same VST3 plugin directly using Steinberg's VST3 SDK?**

This interested me because JUCE makes plugin development significantly easier, but that convenience comes from adding an abstraction layer on top of the underlying plugin format.

To investigate this, I implemented the same simple gain plugin twice:

    once using JUCE
    once directly using the VST3 SDK

The DSP itself was deliberately trivial: each audio sample is multiplied by a gain value. This was important because I wanted to minimise the cost of the DSP algorithm itself and make any measurable difference more likely to come from the surrounding framework.

I then hosted both plugins in Reaper and ran repeated benchmarks under Linux. I used perf to collect CPU cycles and retired instructions, calculated IPC, and also recorded Reaper's own FX CPU measurements.

Before benchmarking, I verified that both implementations actually produced identical output. A standalone C++ test processed the same input through both algorithms and confirmed that the results were bit-exact.

The results were interesting.

The JUCE implementation consistently showed higher CPU usage than the raw VST3 implementation. The difference was small in absolute terms, but it became measurable when running large numbers of plugin instances. At 1000 instances, for example, the Reaper Performance Meter showed roughly 32% more CPU usage for the JUCE implementation.

However, this does not mean that JUCE is a bad choice. In a realistic project using a handful of instances, the absolute overhead is negligible. The main takeaway for me was that framework abstractions do have a measurable cost, even when the underlying DSP is identical.

The project also taught me quite a bit about experimental design. One of the more interesting problems was that hardware-level measurements using perf tracked the entire Reaper process rather than the plugin in isolation, which made very small differences difficult to isolate. Reaper's own plugin CPU meter turned out to give a clearer picture, even though those measurements were collected less rigorously.

I ended up with two open-source implementations, the benchmark scripts, and the full paper.

**This is the repository hosting the source code and analysis scripts.**
