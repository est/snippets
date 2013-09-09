using HttpServer

http = HttpHandler() do req::Request, res::Response
    Response(strig("Hello, World!"))
end

http.events["error"]  = ( client, err ) -> println( err )
http.events["listen"] = ( port )        -> println("Listening on $port...")

server = Server( http )
run( server, 2000 )

