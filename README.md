# wsshuttle
Tunneling into private networks via WinRM
## Usage
`python3 -m wsshuttle -u <username> -i <target jump box> -b <ip for wsshuttle to listen on> -m 192.168.24.0/24`

## How does it work?
- First, wsshuttle establishes a session on the WinRM service indicated
- It then opens a tcp server listening locally on port 6000
- An iptables rule (chain `wsshuttle` in table `netstat`) is added that redirects all traffic to the indicated subnet (`-m` option)
- Upon receiving a redirected connection, the original destination of the connection is retrieved, and a TCP listener is opened
- Meanwhile, a small C# program is uploaded, compiled an executed via PowerShell. It connects to the target service, as well as connecting back to the newly opened TCP listener, and relays traffic between the sockets
- Similarly, the TCP listener is connected to the original connection from the user, and the traffic is relayed over multiple hops to the target service

Upon exiting wsshuttle, the `wsshuttle` iptables chain is set to return instantly, to prevent traffic from being redirected to a closed port.

## Error Handling
WinRM does not seem to be suited to long-running sessions. If an error is detected while running a command, wshuttle will throw away the current shell and open a new one. If *this* fails, the current WinRM session will be discarded, and a new one will be opened. This will be attempted repeatedly - if this process fails 5 times in a row, the connection will be deemed irrecoverable and wsshuttle will exit.