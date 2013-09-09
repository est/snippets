package main

import (
    "net/http" //package for http based web programs
    "fmt"
)

func handler(w http.ResponseWriter, r *http.Request) { 
    fmt.Fprintf(w, "Hello world!")
}

func main() {
    http.HandleFunc("/", handler)
    http.ListenAndServe("0:9999", nil)
}
