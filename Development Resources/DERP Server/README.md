# Local DERP Server

This Compose project runs the official Tailscale DERP server on the local
network:

- DERP: `192.168.1.100:443/tcp`
- STUN: `192.168.1.100:3478/udp`
- DERP map: `http://192.168.1.100:8080/derpmap.json`

The server generates and persists a self-signed certificate for the host IP.
Use the `CertName` pin printed in the container logs when adding this node to a
DERP map. Clients must support pinned IP certificates.

The current node configuration is:

```json
{
  "Name": "local-derp-1",
  "RegionID": 900,
  "HostName": "192.168.1.100",
  "IPv4": "192.168.1.100",
  "DERPPort": 443,
  "STUNPort": 3478,
  "CertName": "sha256-raw:b7af4a29d254dd8c39ba3121c04688cb84cbf8bc73c92bca6a63ee282f2090ae"
}
```

Configure both Tailcat peers with:

```text
--derpmap-url=http://192.168.1.100:8080/derpmap.json
```

The flag is global and must appear before the subcommand or tailcat address.
Start the server first and use the new address it prints:

```powershell
tailcat --derpmap-url=http://192.168.1.100:8080/derpmap.json --verbose serve
tailcat --derpmap-url=http://192.168.1.100:8080/derpmap.json --verbose <new-tailcat-address>
```

Do not reuse an address generated while the server was using another DERP map.
The address's region must resolve to region `900` in this map.

Start or update the server:

```powershell
docker compose up -d --build
```

View the certificate pin and logs:

```powershell
docker compose logs derper
```

Test STUN through the host-published UDP port:

```powershell
docker compose exec derper stunc host.docker.internal 3478
```

Stop the server without deleting its identity or certificate:

```powershell
docker compose down
```

Do not run `docker compose down --volumes` unless you intend to replace the
DERP identity, certificate, and corresponding `CertName` pin.
