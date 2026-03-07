#include <optional>
#include <thread>
#include "zenoh.hxx" // IWYU pragma: keep

static zenoh::Session* session = nullptr;

std::string zid;

bool isConnected = false;

bool leftForkAvailable = false;
bool rightForkAvailable = false;
bool leftForkAcquired = false;
bool rightForkAcquired = false;

// TODO consider limiting broadcast-like message patterns


// table -> single topic -> all philosophers is a broadcast. 
// everyone gets all messages.
// either filter by zid or create unique topics for all philosophers.
// 1. straightforward
// -> more difficult to model
/* 2.
each philosopher sends a connection request;
accept/reject is broadcast with zid attached;
both the table and the philosopher sets up proper topics;
communication continues from these topics.
*/

void callback(const zenoh::Sample &sample){
    auto reply = sample.get_payload().as_string();
    if (reply == "leftForkAvailable") {
        leftForkAvailable = true;
        leftForkAcquired = true;
    }
    else if (reply == "rightForkAvailable") {
        rightForkAvailable = true;
        rightForkAcquired = true;
    }
    else if (reply == "leftForkPutDown") {
        leftForkAvailable = false;
        leftForkAcquired = false;
    }
    else if (reply == "rightForkPutDown") {
        rightForkAvailable = false;
        rightForkAcquired = false;
    }
    else if (reply == "connected") isConnected = true;
}

static std::optional<zenoh::Subscriber<void>> recv;
static std::optional<zenoh::Publisher> send;


void connect(){
    // set up pub & subs
    recv = session->declare_subscriber("phil/" + zid + "/recv", &callback, zenoh::closures::none);
    send = session->declare_publisher("phil/" + zid + "/send");
    // send zenoh id to the table
    session->put("table/connect", zid);
    // wait confirmation from table
    while (!isConnected);
}

int main(){
    using namespace std::chrono_literals;
    auto s = zenoh::Session::open(zenoh::Config::create_default());
    session = &s;
    zid = session->get_zid().to_string();
    // main philosopher logic goes here
    connect();
    enum State {THINKING, HUNGRY, EATING};
    State state = THINKING;

    while (true) {
        std::this_thread::sleep_for(100ms);
        // think unless the left fork is available; when it is, pick it up;
        send->put(zid + ":isLeftForkAvailable");
        if (!leftForkAvailable) continue;
        // think unless the right fork is available; when it is, pick it up;
        send->put(zid + ":isRightForkAvailable");
        if (!rightForkAvailable) continue;
        // when both forks are held, eat for a fixed amount of time;
        state = EATING;
        std::this_thread::sleep_for(2s);
        // put the forks down
        send->put(zid + ":putLeftForkDown");
        send->put(zid + ":putRightForkDown");
        state = THINKING;
    }
}