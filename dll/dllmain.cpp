// dllmain.cpp : Defines the entry point for the DLL application.
#include "pch.h"
#include <stdio.h>;
extern "C" {
    __declspec(dllexport) void foo()
    {
        // here you could use managed and unmanaged code
        
            printf(" \n Hello World");
        }
    }
extern "C" {
    __declspec(dllexport) int MyAdd(int a, int b)
    {
        // here you could use managed and unmanaged code
        
        {
            return a + b;
        }
        
    }
}
extern "C" {
    __declspec(dllexport) char* textreturn(const char* phrase, char* result, size_t resultMaxLength)
    {
        // here you could use managed and unmanaged code

        {
            _snprintf_s(result, resultMaxLength, _TRUNCATE, "Decorated <%s>", phrase);
            return result;
        }

    }
}
