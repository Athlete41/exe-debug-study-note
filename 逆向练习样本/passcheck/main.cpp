#include <iostream>
#include <string>

int main() {
    std::string input_password;
    std::string correct_password = "secret123";
    std::string pause;

    std::cout << "Enter password: ";
    std::cin >> input_password;

    int is_correct = 0;

    if (input_password == correct_password) {
        std::cout << "Access Granted!" << std::endl;
        is_correct = 1;
    } else {
        std::cout << "Access Denied!" << std::endl;
        is_correct = 0;
    }

    system("pause");

    return is_correct;
}