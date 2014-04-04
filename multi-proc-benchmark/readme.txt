test IPC effeciency.


$ time python redis-client.py 
7.74770379066s with 10k loops
haha

real	0m7.814s
user	0m0.024s
sys	0m3.124s



$ time python client.py 
4.83282518387s with 10k loops

real	0m4.910s
user	0m0.032s
sys	0m2.028s
