f=open("/Users/jamie/Downloads/ipsw-from-deflate-stream", "rb")
b=f.read()
for i in range(len(b)-3):
    if b[i] == (~b[i+2] & 0xff) and b[i+1] == (~b[i+3] & 0xff):
        print(i)
        
