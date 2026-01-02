# Network Setup Guide

Detailed guide for configuring network connectivity between PC and Raspberry Pi.

## Table of Contents

- [Network Requirements](#network-requirements)
- [IP Address Configuration](#ip-address-configuration)
- [Firewall Configuration](#firewall-configuration)
- [WiFi vs Ethernet](#wifi-vs-ethernet)
- [Port Forwarding (Advanced)](#port-forwarding-advanced)
- [Troubleshooting](#troubleshooting)

## Network Requirements

### Minimum Requirements

- Both PC and Raspberry Pi on same local network
- Open port 5000 on PC (configurable)
- Stable network connection (Ethernet recommended)
- Bandwidth: 5-10 Mbps minimum for video streaming

### Network Topology

```
[Internet]
    |
[Router/WiFi]
    |
    +--- [PC Server] (192.168.1.100:5000)
    |
    +--- [Raspberry Pi] (192.168.1.101)
```

## IP Address Configuration

### Step 1: Find Your IP Addresses

**On PC (Windows):**
```cmd
ipconfig

# Look for:
# IPv4 Address: 192.168.1.XXX
```

**On PC (Linux/Mac):**
```bash
ifconfig
# or
ip addr show

# Look for:
# inet 192.168.1.XXX
```

**On Raspberry Pi:**
```bash
hostname -I
# or
ifconfig
```

### Step 2: Set Static IP (Recommended)

#### Option A: Static IP on Raspberry Pi

**Edit dhcpcd.conf:**
```bash
sudo nano /etc/dhcpcd.conf
```

**Add at the end:**
```
interface wlan0  # or eth0 for Ethernet
static ip_address=192.168.1.101/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

**Restart networking:**
```bash
sudo systemctl restart dhcpcd
```

#### Option B: Static IP via Router

1. Access router admin panel (usually 192.168.1.1)
2. Find DHCP settings
3. Add DHCP reservation for Pi's MAC address
4. Assign desired IP (e.g., 192.168.1.101)

### Step 3: Update Configuration File

**Edit `config/robot_config.yaml`:**
```yaml
network:
  pc_ip: "192.168.1.100"  # Your PC's actual IP
  pc_port: 5000           # Server port
  pi_ip: "192.168.1.101"  # Your Pi's actual IP
  pi_display_port: 8080
  socketio_namespace_pc: "/pc"
  socketio_namespace_pi: "/pi"
```

### Step 4: Verify Connectivity

**From PC to Pi:**
```bash
ping 192.168.1.101

# Should see replies:
# Reply from 192.168.1.101: bytes=32 time=2ms TTL=64
```

**From Pi to PC:**
```bash
ping 192.168.1.100
```

## Firewall Configuration

### Windows Firewall

**Method 1: GUI**
1. Open Windows Defender Firewall
2. Advanced Settings
3. Inbound Rules -> New Rule
4. Port -> TCP -> 5000
5. Allow the connection
6. Apply to all profiles

**Method 2: PowerShell (Admin)**
```powershell
New-NetFirewallRule -DisplayName "Robot Server" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### Linux Firewall (UFW)

```bash
# Enable UFW
sudo ufw enable

# Allow port 5000
sudo ufw allow 5000/tcp

# Check status
sudo ufw status
```

### macOS Firewall

1. System Preferences -> Security & Privacy
2. Firewall -> Firewall Options
3. Add Python application
4. Allow incoming connections

### Raspberry Pi Firewall

```bash
# Usually no firewall by default
# If iptables configured:
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

## WiFi vs Ethernet

### WiFi Configuration

**Pros:**
- No cables needed
- Flexibility in robot movement

**Cons:**
- Higher latency
- Can drop connection
- Interference issues

**Setup:**
```bash
# On Raspberry Pi
sudo raspi-config
# Network Options -> Wireless LAN
# Enter SSID and password
```

**Optimize WiFi:**
```bash
# Disable WiFi power management
sudo nano /etc/rc.local

# Add before 'exit 0':
/sbin/iwconfig wlan0 power off
```

### Ethernet Configuration

**Pros:**
- Lower latency
- Stable connection
- Better bandwidth

**Cons:**
- Requires cable
- Limits mobility

**Recommended for:**
- Stationary robots
- High-bandwidth applications
- Reliable operation

### Hybrid Approach

For mobile robots:
1. Use WiFi for movement
2. Keep Ethernet as backup
3. Auto-switch in code (advanced)

## Port Configuration

### Default Ports

- **5000**: Flask/SocketIO server (PC)
- **8080**: Face display (Pi)

### Custom Ports

**In `.env`:**
```bash
SERVER_PORT=8000  # Change default port
```

**In `config/robot_config.yaml`:**
```yaml
network:
  pc_port: 8000  # Must match .env
```

### Check Port Usage

**Windows:**
```cmd
netstat -ano | findstr :5000
```

**Linux/Mac:**
```bash
netstat -tuln | grep 5000
# or
lsof -i :5000
```

## Port Forwarding (Advanced)

### Access Over Internet

**Warning:** Only do this if you understand security implications!

1. **Set up port forwarding on router:**
   - External Port: 5000
   - Internal IP: Your PC's IP
   - Internal Port: 5000
   - Protocol: TCP

2. **Find public IP:**
   ```bash
   curl ifconfig.me
   ```

3. **Access from anywhere:**
   ```
   http://YOUR_PUBLIC_IP:5000
   ```

**Security Considerations:**
- Use strong Flask secret key
- Enable HTTPS (SSL/TLS)
- Implement authentication
- Use VPN instead (recommended)

### VPN Alternative (Recommended)

**Use ZeroTier or Tailscale:**

1. Create account at https://tailscale.com
2. Install on both PC and Pi
3. Connect both devices
4. Use VPN IPs in config

**Benefits:**
- Encrypted connection
- No port forwarding
- Access from anywhere
- Better security

## Multiple Robots

### Configuration

For multiple robots on same network:

**Robot 1:**
```yaml
network:
  pi_ip: "192.168.1.101"
  # Use default port 5000
```

**Robot 2:**
```yaml
network:
  pi_ip: "192.168.1.102"
  pc_port: 5001  # Different port!
```

## Troubleshooting

### "Connection Refused"

**Check 1: Server Running**
```bash
ps aux | grep main.py
```

**Check 2: Correct IP**
```bash
# Verify IPs match
ping YOUR_PC_IP
```

**Check 3: Port Open**
```bash
# From Pi, test connection
telnet YOUR_PC_IP 5000
```

### "Connection Timeout"

**Check 1: Firewall**
Disable temporarily to test:
```bash
# Linux
sudo ufw disable

# Windows: Disable in Settings
```

**Check 2: Network Path**
```bash
traceroute YOUR_PC_IP
```

### Intermittent Disconnects

**Solution 1: Static IPs**
See [Static IP Configuration](#step-2-set-static-ip-recommended)

**Solution 2: Better WiFi Signal**
- Move router closer
- Use 5GHz band if available
- Add WiFi extender

**Solution 3: Increase Timeout**
In code, increase connection timeout values.

### High Latency

**Check ping time:**
```bash
ping -c 10 YOUR_PC_IP

# Should be < 10ms on local network
```

**Solutions:**
- Use Ethernet instead of WiFi
- Reduce camera resolution/FPS
- Check for network congestion
- Update router firmware

## Network Testing Tools

### Bandwidth Test

```bash
# Install iperf3
sudo apt-get install iperf3

# On PC (server):
iperf3 -s

# On Pi (client):
iperf3 -c YOUR_PC_IP

# Should show > 10 Mbps for smooth operation
```

### Connection Monitoring

```bash
# Monitor connection
watch -n 1 ping -c 1 YOUR_PC_IP

# Log connection quality
ping YOUR_PC_IP > network_log.txt &
```

## Best Practices

1. **Use static IPs** for both devices
2. **Ethernet over WiFi** when possible
3. **Dedicated network** for robot (separate VLAN)
4. **Regular testing** of connection quality
5. **Backup connection** method (e.g., fallback to hotspot)
6. **Monitor latency** and adjust quality settings
7. **Document your setup** for troubleshooting

## Network Diagram Template

```
┌─────────────────┐
│   Internet      │
└────────┬────────┘
         │
┌────────┴────────┐
│  Router/WiFi    │
│  192.168.1.1    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───┴───┐ ┌───┴───┐
│  PC   │ │  Pi   │
│ .100  │ │ .101  │
│:5000  │ │       │
└───────┘ └───────┘
```

---

**Last Updated:** January 2026