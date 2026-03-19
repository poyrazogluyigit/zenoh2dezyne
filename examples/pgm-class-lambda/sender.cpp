#include <string>
#include <thread>

#include "zenoh.hxx"    // IWYU pragma: keep

int TX_LEAD = 0;
int TX_TRAIL = 0;
int BUF_SIZE = 10;

auto session = zenoh::Session::open(zenoh::Config::create_default());

auto odata = session.declare_publisher("pgm/odata/sn");
auto rdata = session.declare_publisher("pgm/rdata/sn");
auto spm = session.declare_publisher("pgm/spm/sn");

auto nak = session.declare_subscriber("pgm/nak/sn", [](const zenoh::Sample& sample){
    auto missing = std::stoi(sample.get_payload().as_string());
    if (TX_TRAIL < missing) {
        rdata.put(std::to_string(missing));
    }
    else {
        // put unrecoverable
        rdata.put(std::to_string(missing) + ":unrecoverable");
    }
}, zenoh::closures::none);

int main() {

    int ctr = 0;
    for (;;) {
        using namespace std::chrono_literals;
        std::this_thread::sleep_for(10ms);
        spm.put("");
        if (++ctr == 10) {
            odata.put(std::to_string(TX_LEAD++));
            if (TX_LEAD - TX_TRAIL == BUF_SIZE) ++TX_TRAIL;
        }
    }
}