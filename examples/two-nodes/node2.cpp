#include <iostream>
#include <thread>

#include "zenoh.hxx"    // IWYU pragma: keep

using namespace std::literals::chrono_literals;

enum State {
    A, B
};

State state = State::A;

int main(){

    zenoh::Config conf = zenoh::Config::create_default();
    auto session = zenoh::Session::open(std::move(conf));

    auto pub = session.declare_publisher("demo/wrapper/2");

    // bir alttaki tamamen farazi bir ornek
    int x = 0;

    auto sub = session.declare_subscriber("demo/wrapper/1",
        [&pub, &x](const zenoh::Sample& sample) {
        std::cout << sample.get_payload().as_string() << std::endl;
        if (x < 3) {
            state = State::B;
        }
        else if(x >= 3) state = State::A;
        
        x++;
        if (x == 5) 
            x = 0;

        pub.put(std::to_string(static_cast<int>(state)));
        }, zenoh::closures::none);

    while (1){
        // pub.put("Sent from 2");
        std::this_thread::sleep_for(200ms);
    }

    return 0;
}