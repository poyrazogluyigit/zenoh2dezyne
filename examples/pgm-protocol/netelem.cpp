#include <thread>
#include "zenoh.hxx"    // IWYU pragma: keep

auto session = zenoh::Session::open(zenoh::Config::create_default());

auto odata_rdir = session.declare_publisher("pgm/odata/nr");
void odata_cb(const zenoh::Sample& sample) {
    // TODO consider delay logic here
    odata_rdir.put(sample.get_payload().as_string());
}
auto odata = session.declare_subscriber("pgm/odata/sn", &odata_cb, zenoh::closures::none);

auto rdata_rdir = session.declare_publisher("pgm/rdata/nr");
void rdata_cb(const zenoh::Sample& sample) {
     // TODO consider delay logic here
    rdata_rdir.put(sample.get_payload().as_string());   
}
auto rdata = session.declare_subscriber("pgm/rdata/sn", &rdata_cb, zenoh::closures::none);

auto spm_rdir = session.declare_publisher("pgm/spm/nr");
void spm_cb(const zenoh::Sample& sample) {
     // TODO consider delay logic here
    spm_rdir.put(sample.get_payload().as_string());   
}
auto spm = session.declare_subscriber("pgm/spm/sn", &spm_cb, zenoh::closures::none);

int main(){

    for (;;) {
        using namespace std::chrono_literals;
        std::this_thread::sleep_for(1ms);
    }
}