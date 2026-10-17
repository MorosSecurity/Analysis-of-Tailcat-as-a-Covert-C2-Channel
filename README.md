# Analysis of Tailcat as a Covert C2 Channel

## The Question
Do Suricata's "Emerging Threats" ruleset identify Tailcat when used as a covert C2 Channel, and is Tailcat a suitable covert C2 channel?

## A Not Much Shorter TL;DR
We have provided Suricata rules for defenders as well as resources to simplify development for Red teamers and probably malicious actors, but please don't use these... The tools have cooties if your a malicious threat actor. These can be found on our Github along with this report.

For using the default Tailcat binary and the Tailscale provided DERP servers its easier from the defenders perspective to identify and prevent on the network side, as there are IoCs that when blocked would prevent use of Tailcat and for the red teamers this deployment is the most low effort, low resource development and possibly the lowest OPSEC risk. 

For the default Tailcat binary and custom DERP server from the defenders perspective identifying and preventing Tailcat requires further looking at packets. The IoCs are a little less observable but still possible although, depending on how the adversary deploys their DERP server the defender could easily identify Tailcat usage. For the red teamers there is a bigger OPSEC risk and investment required on resource development, although its fairly hard to determine what is specifically Tailcat usage.

For the custom binary and custom DERP server where the IoCs found in the default Tailcat client are refactored then for the defenders we believe that this can be far more challenging to identify. Identifying specifically Tailcat usage is challenging, you are more likely to identify the binary than the communication channel although some of the IoCs found may still be applicable it just depends on the adversaries execution. The best bet is to look at the behaviour of the C2 in whatever killchain they have executed. For the red teamers, this is a higher OPSEC risk, high resource investment, and higher complexity. If everything before and after the C2 is perfect and the defenders struggle connecting dots then your set, but the C2 alone will be challenging to detect depending on the environment. We did explore this capability but are leaving findings out of this report.

Identifying Tailcat being used as a C2 is challenging because it can be hard to identify if whats communicating is Tailcat, Tailscale, or just Wireguard depending on visibility. As with security in general, it is important to have multiple data points for identification in your analysis.
## Background
Recently there has been a lot of conversation around a tool released by Tailscale called "Tailcat" which is essentially a Tailscale implementation of Netcat a tool for network administrators. The Tailcat tool is a portable binary that does not require privileges to execute or authentication to Tailscale. The binary allows for various features including remote access, file transfer, and other data transmission needs.

As soon as we saw this tool we recognized the impact that it could have on security. Each connection is a unique Wireguard based connection, and its widely used so it could be fairly challenging to determine what is malicious and what is not. If it doesn't require authentication to the control plane or need a Tailscale account then the challenge becomes distinguishing the difference between Tailscale and Tailcat, and what is legitimate usage and what is not.

The main use case that we found which was quite impactful was for covert Command and Control `[TA0011]` from a adversary perspective a C2 using Tailcat would have the following benefits:
- Encrypted connections using Wireguard
- Uses a common protocol like NAT Traversal via STUN (used for WebRTC and SIP like Teams, Discord, and VoIP as well as for gaming)
- No authentication to the Control Plane or a Tailscale account required
- Limited information exchange to establish the C2 channel (Only need to share the TC string identifier)
- No installation required, Portable binary
- Open-source codebase for accessibility to custom development
- Pre-built binary with file sharing, ssh, and various other capabilities.
- No IP specific routing knowledge required.

We decided to investigate what this type of channel would look like, identify the behaviour and see if there is any indicators that can be used to identify this C2 channel. How the tool gets deployed is out of scope as well as how the TC address is known/exchanged since there's a million ways to skin a cat.... get it?... cause Tail-cat. 

We did determine that there are 3 possible ways to utilize this method of C2 but only explored the first two for this report:
1. Using the default Tailcat binary, and Tailcat/Tailscale provided DERP servers
2. Using the default Tailcat binary, and a custom DERP server using DERPER (another Tailscale product)
3. Using a custom Tailcat binary/code, and a custom DERP server using DERPER

## Findings - Default Tailcat binary
During our initial testing of the Tailcat binary we decided it would be best to conduct tests with the program as is. This offers the lowest barrier to entry for red teamers/malicious actors. It is quick and easy to deploy but comes with more indicators than the other methods we tested. 

### Analysis 
The biggest indicator of running Tailcat with its default configuration is that upon execution Tailcat reaches out to `tailcat.dev`. By default Tailcat uses `tailcat.dev` which hosts its default DERP map which is accessed by a TCP connection. The "Victim" sends a SYN packet to establish a connection to `tailcat.dev`. After the connection is established we see: 

```
Client Hello (SNI=tailcat.dev)
```

Immediately after this connection is established, STUN traffic is observed. Tailcat uses STUN to find the Adversary public facing IP so both Victim and Adversary can communicate directly. 

```
STUN	82	Binding Request
STUN	74	Binding Success Response XOR-MAPPED-ADDRESS: <IP>:<port>
```

It is likely you will see multiple `Binding Success Response XOR-MAPPED-ADDRESS: <IP>:<port> ` with the same IP and different ports, but the Binding request has the destination port of UDP/3478. Once Tailcat is finished its host-discovery phase the Victim will establish a TLS1.3 connection to the DERP server.

```
tc<Truncated Public Key>.ipn.dev
```

Tailcat has now successfully established communications with the Adversary. Right before the traffic transitions into a WireGuard tunnel, we will see Tailscale Discovery (DISCO) UDP packets. Within the UDP packet under the data we will see the HEX below: 

```
54 53 f0 9f 92 ac
```

When this hex is decoded to UTF-8 it reads: 

```
TS💬
```

Tailcat will now transition to Wireguard to communicate.

## Findings - Custom DERP Server
During our test we found that the Victim sent STUN binding requests to multiple public servers on UDP/3478 which contained the string:

```
SOFTWARE: tailnode
```

The STUN responses from one of the public servers reported varying mapped ports demonstrating NAT endpoint discovery.

Victim then initiated TLS1.3 to our Self hosted `derpmap.json` asset web server on TCP/443 with the string:

```
SNI: <DERPSERVER>.ipn.dev
```

Where `<DERPSERVER>` is a unique value for the DERP server that Tailcat uses, this value is the hostname of the DERP server in the TC address. You can see the DERP servers hostname and IP values from the TC address using the command `tailcat parse <TC_address>`

The Adversary then begins sending a direct UDP packet with a payload to Victim beginning with:

```hex
54 53 f0 9f 92 ac
```

When decoded from Hex to UTF-8 it reads:

```
TS💬
```

Which is the Tailscale peer-discovery protocol marker. The discovery exchange was then followed by Wireguard-style handshake/transport packets between the two hosts Adversary <-> Victim

This indicates that Tailcat discovered and established a direct UDP path between the peers. This is also partially indicative of regular Tailscale behaviour.

## Defender Limitations
Since DERP communications occur inside TLS then without session keys or endpoint logs a capture would not be able to inspect the DERP application protocol or determine exactly how much peer data traversed the relay. Since the Direct UDP connection is using Wireguard it is unlikely to see what is being communicated using network analysis. The IoCs mentioned can indicate such a connection but an adversary refactor of the DERP server and Tailcat client would be challenging and possible void these IoCs.

## Red Team Limitations
We did find that transfer of data from Adversary to Victim was done through a direct UDP connection using Wireguard, exposing the Adversary IP. We tested this with Adversary and Victim being on the same LAN, and as well as on two separate networks from two separate ISPs. What we found was that the channel was a direct UDP connection exposing the Adversary IP. Since Tailscales data plane is a P2P meshed ZTNA layer we assumed that this behaviour is caused due too geographical location of the devices and so we did attempt to have the Adversary machine in a different geographical area (a VPS in Warsaw, Poland) but it was unable to establish the connection using the custom DERP server. We then attempted the Tailcat connection using the default DERP servers provided by Tailscale and were able to establish the connection showing the direct UDP connection still exposing Adversary IP. We believe the failure to establish the connection between Warsaw Adversary and Victim using a custom DERP server was caused by some sort of geographical limitation. We do not fully know the reason that this didn't work.

The assumption that we have made about the direct UDP connection behaviour is default to Tailcat. In Tailscale there is the Control plane, and so for devices to make a connection they first have to authenticate and connect to the Tailnet, receive their Tailnet IP and then they make the direct UDP connection using that Tailnet IP. Since Tailcat requires no authentication to the Control plane or a Tailcale account, the direct UDP connection is established using the Adversary and Victim IPs resulting in a possible OPSEC challenge.

## Conclusion
In our captures, the Suricata ET ruleset detected generic STUN activity but did no specifically identify Tailcat or classify the channel as a command and control. We believe that classifying the traffic as command and control is much better placed on the host by identifying the behaviour around the connection through host based analysis. Although there were no supporting ET rules for this, we did write some which can be found in the Github repository containing this report.

Tailcat can provide an encrypted transport suitable for legitimate administration or misuse as C2. The observed network behaviours expose recognizable Tailscale derived protocol fingerprints, but most are not uniquely attributable to Tailcat or malicious activity. Network based analysis is challenging for defenders, and so use of Tailcat for covert C2 by adversaries is profitable.