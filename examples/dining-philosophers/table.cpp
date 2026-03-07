#include <optional>
#include <string>
#include <thread>

#include "zenoh.hxx"        // IWYU pragma: keep

#define NUM_PHIL 5

struct Connection {
    std::string zid;
    std::optional<zenoh::Publisher> send;
    std::optional<zenoh::Subscriber<void>> recv;
};


bool forks[NUM_PHIL-1]{1};
Connection phils[NUM_PHIL];

static zenoh::Session* session = nullptr;

// we need a better approach
int get_phil_id(std::string zid) {
    for (int i = 0; i < NUM_PHIL; i++) {
        if (phils[i].zid == zid) return i;
    }
    return -1;
}

void table_callback(const zenoh::Sample& sample){
    auto reply = sample.get_payload().as_string();
    auto pos = reply.find(":");
    std::string zid = reply.substr(0, pos);
    std::string req = reply.substr(pos+1, reply.size()-pos-1);
    int phil_id = get_phil_id(zid);
    int left_id = phil_id - 1 < 0 ? NUM_PHIL - 1 : phil_id - 1;
    int right_id = phil_id + 1 == NUM_PHIL ? 0 : phil_id + 1;
    if (req == "isLeftForkAvailable") {
        if (forks[left_id]) {
            forks[left_id] = false;
            phils[phil_id].send->put("leftForkAvailable");
        }
    }
    if (req == "isRightForkAvailable") {
        if (forks[right_id]) {
            forks[right_id] = false;
            phils[phil_id].send->put("rightForkAvailable");
        }
    }
    if (req == "putLeftForkDown") {
        forks[left_id] = true;
    }
    if (req == "putRightForkDown") {
        forks[right_id] = true;
    }
}

void register_phil(const zenoh::Sample& sample){
    static int phil_id = 0;
    auto incoming_zid = sample.get_payload().as_string();
    if (phil_id >= NUM_PHIL) return;
    phils[phil_id].zid = incoming_zid;
    phils[phil_id].recv = session->declare_subscriber("table/" + incoming_zid + "/send", &table_callback, zenoh::closures::none);
    phils[phil_id].send = session->declare_publisher("table/" + incoming_zid + "/recv");
    phils[phil_id].send->put("connected");
    phil_id++;
}

int main(){
    using namespace std::chrono_literals;
    auto s = zenoh::Session::open(zenoh::Config::create_default());
    session = &s;
    auto sub = session->declare_subscriber(
        "table/connect", &register_phil, zenoh::closures::none
    );

    for (;;) std::this_thread::sleep_for(1ms);
}