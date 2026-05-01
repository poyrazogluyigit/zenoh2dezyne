#include <thread>
#include "zenoh.hxx"    // IWYU pragma: keep

int main() {

    auto session = zenoh::Session::open(zenoh::Config::create_default());

    auto B_pub = session.declare_publisher("basic/B/A");
    auto C_pub = session.declare_publisher("basic/C/A");

    while (true) {
        using namespace std::chrono_literals;
        std::this_thread::sleep_for(50ms);
        B_pub.put("example-payload");
    }
}