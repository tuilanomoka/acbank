#!/usr/bin/env python3
import socket
import sys
import os

def check_socket():
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect('/home/nmk/acbank/acbank.sock')
        
        # Send simple HTTP request
        sock.send(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        response = sock.recv(1024)
        sock.close()
        
        if b"200 OK" in response or b"302" in response:
            print("✓ AC Bank healthy")
            return True
        else:
            print("✗ AC Bank response error")
            return False
            
    except Exception as e:
        print(f"✗ AC Bank socket error: {e}")
        return False

if __name__ == "__main__":
    if not check_socket():
        print("Restarting AC Bank...")
        os.system("sudo supervisorctl restart acbank")
        sys.exit(1)
    else:
        sys.exit(0)
