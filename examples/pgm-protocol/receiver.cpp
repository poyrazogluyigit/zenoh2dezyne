#include "zenoh.hxx"    // IWYU pragma: keep
#include <thread>

int LAST_RECEIVED = -1;

auto session = zenoh::Session::open(zenoh::Config::create_default());

auto nak = session.declare_publisher("pgm/nak/nr");

void data_cb(const zenoh::Sample& sample){
    auto seq = std::stoi(sample.get_payload().as_string());
    if (LAST_RECEIVED + 1 == seq) LAST_RECEIVED = seq;
    else nak.put(std::to_string(LAST_RECEIVED+1));
}

auto odata = session.declare_subscriber("pgm/odata/nr", data_cb, zenoh::closures::none);
auto rdata = session.declare_subscriber("pgm/rdata/nr", data_cb, zenoh::closures::none);

int main(){

    for (;;){
        using namespace std::chrono_literals;
        std::this_thread::sleep_for(1ms);
    }

}