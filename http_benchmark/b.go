
package main
 
import (
	"net"
	"os"
)
 
func main() {
	println("Starting the server")
 
	listener, err := net.Listen("tcp", "0.0.0.0:6666")
	if err != nil {
		println("error listening:", err.Error())
		os.Exit(1)
	}
 
	for {
		conn, err := listener.Accept()
		if err != nil {
			println("Error accept:", err.Error())
			return
		}
		go EchoFunc(conn)
	}
}
 
func EchoFunc(conn net.Conn) {
	buf := make([]byte, 10)
	_, err := conn.Read(buf)
	if err != nil {
		println("Error reading:", err.Error())
		return
	}
 
	//send reply
	t := []byte("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nHello, World!")
	_, err = conn.Write(t)
	if err != nil {
		println("Error send reply:", err.Error())
	}
	conn.Close()
}
