cmake_minimum_required(VERSION 3.20)
project(reg_gcwii_web_surface LANGUAGES CXX)

if(NOT EMSCRIPTEN)
  message(FATAL_ERROR "This probe must be configured through emcmake/Emscripten")
endif()

add_executable(reg_gcwii_web_surface main.cpp)
target_compile_features(reg_gcwii_web_surface PRIVATE cxx_std_20)

# Modern Emscripten removed -sUSE_WEBGPU. Emdawnwebgpu provides Dawn's
# webgpu.h/webgpu_cpp.h API on top of the browser WebGPU implementation.
target_compile_options(reg_gcwii_web_surface PRIVATE
  "SHELL:--use-port=emdawnwebgpu"
)
target_link_options(reg_gcwii_web_surface PRIVATE
  "SHELL:--use-port=emdawnwebgpu"
  "SHELL:--shell-file ${CMAKE_CURRENT_SOURCE_DIR}/shell.html"
  "-sASSERTIONS=1"
)

set_target_properties(reg_gcwii_web_surface PROPERTIES SUFFIX ".html")
