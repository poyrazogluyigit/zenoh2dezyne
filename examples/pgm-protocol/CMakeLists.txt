cmake_minimum_required(VERSION 3.8)
set(CMAKE_CXX_STANDARD 20)

project(PGMProtocol)

find_package(zenohc REQUIRED)
message(STATUS "Using ZenohC ${zenohc_VERSION}")    

find_package(zenohcxx REQUIRED)
message(STATUS "Using ZenohC++ ${zenohcxx_VERSION}") 

add_executable(netelem netelem.cpp)
target_link_libraries(netelem PUBLIC zenohcxx::zenohc)

add_executable(receiver receiver.cpp)
target_link_libraries(receiver PUBLIC zenohcxx::zenohc)

add_executable(sender sender.cpp)
target_link_libraries(sender PUBLIC zenohcxx::zenohc)