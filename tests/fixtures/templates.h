// templates.h
#pragma once

template<typename T>
class Holder {
public:
    Holder();
    ~Holder();
    T value;
};
