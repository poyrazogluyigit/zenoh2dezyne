cmake_minimum_required(VERSION 3.8)
set(CMAKE_CXX_STANDARD 20)

project(DiningPhilosophersExample)

find_package(zenohc REQUIRED)
message(STATUS "Using ZenohC ${zenohc_VERSION}")    

find_package(zenohcxx REQUIRED)
message(STATUS "Using ZenohC++ ${zenohcxx_VERSION}") 

add_executable(philosopher philosopher.cpp)
target_link_libraries(philosopher PUBLIC zenohcxx::zenohc)

add_executable(table table.cpp)
target_link_libraries(table PUBLIC zenohcxx::zenohc)