#include <thread>
#include <zenoh.hxx>    // IWYU pragma: keep

int main() {

    auto session = zenoh::Session::open(zenoh::Config::create_default());

    auto A_pub = session.declare_publisher("basic/A/C");
    auto B_pub = session.declare_publisher("basic/B/C");

    bool pubSelect = false;

    auto AB_callback = [&](){
        if (pubSelect) A_pub.put("example payload to A");
        else B_pub.put("example payload to B");
        pubSelect = !pubSelect;
    };

    auto A_sub = session.declare_subscriber("basic/C/A", &AB_callback, zenoh::closures::none);
    auto C_sub = session.declare_subscriber("basic/C/B", &AB_callback, zenoh::closures::none);


    while (true) {
        using namespace std::chrono_literals;
        std::this_thread::sleep_for(50ms);
    }
}