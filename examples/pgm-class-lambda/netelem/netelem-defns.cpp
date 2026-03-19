#include "netelem.h"

int LAST_RECEIVED = -1;

auto session = zenoh::Session::open(zenoh::Config::create_default());
auto nak = session.declare_publisher("pgm/nak/nr");

auto odata = session.declare_subscriber("pgm/odata/nr", [](const zenoh::Sample& sample){
    auto seq = std::stoi(sample.get_payload().as_string());
    if (LAST_RECEIVED + 1 == seq) LAST_RECEIVED = seq;
    else nak.put(std::to_string(LAST_RECEIVED+1));
}, zenoh::closures::none);

auto rdata = session.declare_subscriber("pgm/rdata/nr", [](const zenoh::Sample& sample){
    auto seq = std::stoi(sample.get_payload().as_string());
    if (LAST_RECEIVED + 1 == seq) LAST_RECEIVED = seq;
    else nak.put(std::to_string(LAST_RECEIVED+1));
}, zenoh::closures::none);