cmake_minimum_required(VERSION 3.20)
project(reg_n64_web_host LANGUAGES CXX)

add_library(reg_n64_web_host STATIC src/n64_web_host.cpp)
target_include_directories(reg_n64_web_host PUBLIC include)
target_compile_features(reg_n64_web_host PUBLIC cxx_std_20)

add_executable(reg_n64_web_smoke src/smoke_main.cpp)
target_link_libraries(reg_n64_web_smoke PRIVATE reg_n64_web_host)
target_compile_features(reg_n64_web_smoke PRIVATE cxx_std_20)

if(EMSCRIPTEN)
    set_target_properties(reg_n64_web_smoke PROPERTIES SUFFIX ".html")
    target_link_options(reg_n64_web_smoke PRIVATE
        "-sALLOW_MEMORY_GROWTH=1"
        "-sASSERTIONS=1"
    )
else()
    message(STATUS "Native host build: web APIs are compiled as safe stubs")
endif()
