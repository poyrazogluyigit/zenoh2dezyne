#include "netelem.h"    // IWYU pragma: keep
#include <thread>

int main(){

    for (;;){
        using namespace std::chrono_literals;
        std::this_thread::sleep_for(1ms);
    }  

}