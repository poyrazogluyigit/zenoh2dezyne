#include <thread>
#include "zenoh.hxx"    // IWYU pragma: keep

void C_callback(const zenoh::Sample&) {
    return;
}

int main() {

    auto session = zenoh::Session::open(zenoh::Config::create_default());

    auto A_pub = session.declare_publisher("basic/A/B");
    auto C_pub = session.declare_publisher("basic/C/B");

    auto A_callback = [&](const zenoh::Sample&){
        for (int i = 0; i < 5; i++) {
            C_pub.put("example payload to C");
        }
        A_pub.put("example payload to A");
    };

    auto A_sub = session.declare_subscriber("basic/B/A", &A_callback, zenoh::closures::none);
    auto C_sub = session.declare_subscriber("basic/B/C", &C_callback, zenoh::closures::none);


    while (true) {
        using namespace std::chrono_literals;
        std::this_thread::sleep_for(50ms);
    }
}