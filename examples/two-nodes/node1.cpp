#include <iostream>
#include <thread>
#include <zenoh/api/closures.hxx>

#include "zenoh.hxx"    // IWYU pragma: keep

using namespace std::literals::chrono_literals;

int main(){

    zenoh::Config conf = zenoh::Config::create_default();
    auto session = zenoh::Session::open(std::move(conf));

    auto pub = session.declare_publisher("demo/wrapper/1");
    auto sub = session.declare_subscriber("demo/wrapper/2",
    [](const zenoh::Sample &sample){
        std::cout << "Received " << sample.get_payload().as_string() << std::endl;
    }, zenoh::closures::none);

    while (1){
        std::string input;
        std::cin >> input;
        pub.put(input);
        std::this_thread::sleep_for(200ms);
    }

    return 0;
}