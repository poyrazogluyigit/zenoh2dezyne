#include "zenoh.hxx"

// tek mesaja dusur
// pure fonksiyon assumptioni yapilabilir
// 
void cb(){

}

int main(){
    zenoh::Config conf = zenoh::Config::create_default();
    auto sess = zenoh::Session::open(std::move(conf));

    auto pub = sess.declare_publisher("example/2");

    bool var = false;

    auto sub = sess.declare_subscriber("example", [&](const zenoh::Sample &sample){
        for (int i = 0; i < 10; i++){
        pub.put(std::to_string(i));

        if (i % 2 == 0) var = true;
        else var = false;
    }
    }, 
    zenoh::closures::none);

    for(;;){

    }
    return 0;
}