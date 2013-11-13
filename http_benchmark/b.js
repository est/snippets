var http = require("http");
http.globalAgent.maxSockets = 128;

http.createServer(function(request, response) {
  response.writeHead(200, {"Content-Type": "application/json"});
  var r = {name: 'A Royal Baby', body:'A slow news week'}
  response.write(JSON.stringify(r));
  response.end();
}).listen(8888);

