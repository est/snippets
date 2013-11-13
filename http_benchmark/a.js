var http = require("http");

/*  https://news.ycombinator.com/item?id=6717672 */
http.globalAgent.maxSockets = 128;

http.createServer(function(request, response) {
  response.writeHead(200, {"Content-Type": "text/plain"});
  response.write("Hello World");
  response.end();
}).listen(8888);

