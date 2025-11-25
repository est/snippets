import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

def scan_port(host, port, timeout=0.5):
    """Return True if port is open, False otherwise."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except:
            return False

def scan_range(host, start_port, end_port, workers=100):
    """Scan a range of ports using a thread pool."""
    open_ports = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(scan_port, host, port): port
            for port in range(start_port, end_port + 1)
        }

        for future in as_completed(futures):
            port = futures[future]
            if future.result():
                open_ports.append(port)

    return sorted(open_ports)

if __name__ == "__main__":
    host = input("Host to scan: ").strip()
    start_port = int(input("Start port: "))
    end_port = int(input("End port: "))

    print(f"\nScanning {host} ports {start_port}-{end_port}...\n")
    open_ports = scan_range(host, start_port, end_port)

    if open_ports:
        print("Open ports:")
        for p in open_ports:
            print("  ", p)
    else:
        print("No open ports found.")

