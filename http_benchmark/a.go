package main

import (
    "encoding/json"
    "fmt"
    "github.com/emicklei/go-restful"
    "io"
    "net/http"
)

func main() {
    ws := new(restful.WebService)
    ws.Route(ws.GET("/").To(hello))
    restful.Add(ws)
    fmt.Print("Server starting on port 8085\n")
     http.ListenAndServe(":8085", nil)
}

func hello(req *restful.Request, resp *restful.Response) {
    article := Article{"A Royal Baby", "A slow news week"}
    b, _ := json.Marshal(article)
    io.WriteString(resp, string(b))
}

type Article struct {
    Name string
    Body string
}

