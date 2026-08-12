#include "cracker_installer.hpp"
#include <iostream>
#include <iomanip>
#include <array>
#include <cstring>
#include <optional>
#include <thread>
#include <chrono>


int main() {

    if (cracker_installer::UninstallDriver()) {
        std::cout << "[+] Device uninstall successfully." << std::endl;
    }
    else {
        std::cerr << "[-] Failed to uninstall driver." << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        return 1;
    }

    if (cracker_installer::InstallDriver()) {
        std::cout << "[+] Device install successfully." << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        return 0;
    }
    else {
        std::cerr << "[-] Failed to install driver." << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        return 1;
    }
}