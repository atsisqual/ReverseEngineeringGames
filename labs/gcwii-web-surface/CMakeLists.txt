cmake_minimum_required(VERSION 3.20)
project(reg_gcwii_web_surface LANGUAGES CXX)

if(NOT EMSCRIPTEN)
  message(FATAL_ERROR "This probe must be configured through emcmake/Emscripten")
endif()

function(add_gcwii_webgpu_probe target source)
  add_executable(${target} ${source})
  target_compile_features(${target} PRIVATE cxx_std_20)

  # Modern Emscripten removed -sUSE_WEBGPU. Emdawnwebgpu provides Dawn's
  # webgpu.h/webgpu_cpp.h API on top of the browser WebGPU implementation.
  target_compile_options(${target} PRIVATE
    "SHELL:--use-port=emdawnwebgpu"
  )
  target_link_options(${target} PRIVATE
    "SHELL:--use-port=emdawnwebgpu"
    "SHELL:--shell-file ${CMAKE_CURRENT_SOURCE_DIR}/shell.html"
    "-sASSERTIONS=1"
  )
  set_target_properties(${target} PROPERTIES SUFFIX ".html")
endfunction()

add_gcwii_webgpu_probe(reg_gcwii_web_surface main.cpp)
add_gcwii_webgpu_probe(reg_gcwii_web_device device_bootstrap.cpp)
target_link_options(reg_gcwii_web_device PRIVATE "-sNO_EXIT_RUNTIME=1")

# Aurora's public initialize contract is synchronous today. This probe shows how
# that contract can be retained on the web while still yielding to async WebGPU.
add_gcwii_webgpu_probe(reg_gcwii_web_syncbridge sync_bridge.cpp)
target_link_options(reg_gcwii_web_syncbridge PRIVATE "-sASYNCIFY=1")
