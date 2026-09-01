cmake_minimum_required(VERSION 3.14.0)
set(CMAKE_OSX_DEPLOYMENT_TARGET 10.13 CACHE STRING "")

project(SimpleGainSDK
    VERSION 1.0.0.0
    DESCRIPTION "SimpleGainSDK VST 3 Plug-in"
)

add_subdirectory(external)

smtg_enable_vst3_sdk()

smtg_add_vst3plugin(SimpleGainSDK
    source/version.h
    source/cids.h
    source/processor.h
    source/processor.cpp
    source/controller.h
    source/controller.cpp
    source/entry.cpp
)

target_link_libraries(SimpleGainSDK
    PRIVATE
        sdk
)

smtg_target_configure_version_file(SimpleGainSDK)

if(SMTG_MAC)
    smtg_target_set_bundle(SimpleGainSDK
        BUNDLE_IDENTIFIER com.robranch.simplegain
        COMPANY_NAME "Rob's plugins"
    )
    smtg_target_set_debug_executable(SimpleGainSDK
        "/Applications/VST3PluginTestHost.app"
        "--pluginfolder;$(BUILT_PRODUCTS_DIR)"
    )
elseif(SMTG_WIN)
    target_sources(SimpleGainSDK PRIVATE 
        resource/win32resource.rc
    )
    if(MSVC)
        set_property(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY VS_STARTUP_PROJECT SimpleGainSDK)

        smtg_target_set_debug_executable(SimpleGainSDK
            "$(ProgramW6432)/Steinberg/VST3PluginTestHost/VST3PluginTestHost.exe"
            "--pluginfolder \"$(OutDir)/\""
        )
    endif()
endif(SMTG_MAC)
