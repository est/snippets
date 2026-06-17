import asyncio
import argparse
from typing import Optional


async def scan_port(host: str, port: int, timeout: float) -> Optional[int]:
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return port
    except (asyncio.TimeoutError, OSError):
        return None


async def scan(host: str, ports: list[int], timeout: float, concurrency: int) -> list[int]:
    sem = asyncio.Semaphore(concurrency)
    open_ports: list[int] = []

    async def _scan(port: int):
        async with sem:
            result = await scan_port(host, port, timeout)
            if result is not None:
                open_ports.append(result)
                print(f"[OPEN] {host}:{port}")

    await asyncio.gather(*(_scan(p) for p in ports))
    return sorted(open_ports)


def parse_ports(spec: str) -> list[int]:
    ports = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            ports.extend(range(int(lo), int(hi) + 1))
        else:
            ports.append(int(part))
    return sorted(set(ports))


async def main():
    parser = argparse.ArgumentParser(description="Async TCP port scanner")
    parser.add_argument("host", help="Target host")
    parser.add_argument(
        "-p", "--ports", default="1-1024", help="Port range, e.g. 80,443 or 1-1024"
    )
    parser.add_argument("-t", "--timeout", type=float, default=1.0, help="Connect timeout in seconds")
    parser.add_argument("-c", "--concurrency", type=int, default=500, help="Max concurrent connections")
    args = parser.parse_args()

    ports = parse_ports(args.ports)
    print(f"Scanning {args.host} ({len(ports)} ports, concurrency={args.concurrency}) ...")

    open_ports = await scan(args.host, ports, args.timeout, args.concurrency)

    print(f"\nDone. {len(open_ports)} open port(s):")
    for p in open_ports:
        print(f"  {p}")


if __name__ == "__main__":
    asyncio.run(main())
