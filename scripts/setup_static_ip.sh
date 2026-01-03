#!/bin/bash

# Static IP Configuration Script for Distributed Robot System
# Usage: sudo ./setup_static_ip.sh [pc|pi]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Get device type
DEVICE_TYPE="$1"

if [[ -z "$DEVICE_TYPE" ]]; then
    echo -e "${RED}Usage: sudo $0 [pc|pi]${NC}"
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  sudo $0 pc   # Configure PC server"
    echo -e "  sudo $0 pi   # Configure Raspberry Pi"
    exit 1
fi

if [[ "$DEVICE_TYPE" != "pc" && "$DEVICE_TYPE" != "pi" ]]; then
    echo -e "${RED}Error: Device type must be 'pc' or 'pi'${NC}"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Static IP Setup - Distributed Robot System        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Detect network interface
echo -e "${YELLOW}Detecting network interfaces...${NC}"
INTERFACES=$(ip -o link show | awk -F': ' '{print $2}' | grep -v "lo\|docker\|veth")
echo -e "${GREEN}Available interfaces:${NC}"
echo "$INTERFACES"
echo ""

# Auto-detect active interface
ACTIVE_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)

if [[ -z "$ACTIVE_INTERFACE" ]]; then
    echo -e "${RED}No active network interface found!${NC}"
    echo -e "${YELLOW}Please connect to a network and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}Active interface detected: $ACTIVE_INTERFACE${NC}"
echo ""

# Get current network info
CURRENT_IP=$(ip -4 addr show "$ACTIVE_INTERFACE" | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
CURRENT_GATEWAY=$(ip route | grep default | awk '{print $3}' | head -n1)
CURRENT_DNS=$(grep "nameserver" /etc/resolv.conf | head -n1 | awk '{print $2}')

echo -e "${BLUE}Current Network Configuration:${NC}"
echo -e "  Interface: ${GREEN}$ACTIVE_INTERFACE${NC}"
echo -e "  IP Address: ${GREEN}${CURRENT_IP:-Not assigned}${NC}"
echo -e "  Gateway: ${GREEN}${CURRENT_GATEWAY:-Not found}${NC}"
echo -e "  DNS: ${GREEN}${CURRENT_DNS:-Not found}${NC}"
echo ""

# Recommended IPs based on device type
if [[ "$DEVICE_TYPE" == "pc" ]]; then
    RECOMMENDED_IP="192.168.1.100"
    OTHER_DEVICE="Raspberry Pi"
    OTHER_IP="192.168.1.101"
else
    RECOMMENDED_IP="192.168.1.101"
    OTHER_DEVICE="PC Server"
    OTHER_IP="192.168.1.100"
fi

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Recommended Configuration for $DEVICE_TYPE:${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "  Static IP: ${GREEN}$RECOMMENDED_IP${NC}"
echo -e "  Gateway: ${GREEN}${CURRENT_GATEWAY:-192.168.1.1}${NC}"
echo -e "  DNS: ${GREEN}8.8.8.8, 8.8.4.4${NC}"
echo -e "  $OTHER_DEVICE IP: ${GREEN}$OTHER_IP${NC}"
echo ""

# Get user input
read -p "Enter static IP address [$RECOMMENDED_IP]: " STATIC_IP
STATIC_IP=${STATIC_IP:-$RECOMMENDED_IP}

read -p "Enter gateway/router IP [${CURRENT_GATEWAY:-192.168.1.1}]: " GATEWAY
GATEWAY=${GATEWAY:-${CURRENT_GATEWAY:-192.168.1.1}}

read -p "Enter DNS server [8.8.8.8]: " DNS1
DNS1=${DNS1:-8.8.8.8}

DNS2="8.8.4.4"

read -p "Enter subnet prefix [24]: " PREFIX
PREFIX=${PREFIX:-24}

echo ""
echo -e "${BLUE}Configuration Summary:${NC}"
echo -e "  Interface: ${GREEN}$ACTIVE_INTERFACE${NC}"
echo -e "  Static IP: ${GREEN}$STATIC_IP/$PREFIX${NC}"
echo -e "  Gateway: ${GREEN}$GATEWAY${NC}"
echo -e "  DNS: ${GREEN}$DNS1, $DNS2${NC}"
echo ""

read -p "Apply this configuration? (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo -e "${YELLOW}Configuration cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Configuring static IP...${NC}"

# Backup existing configuration
BACKUP_DIR="/root/network_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Detect network manager
if systemctl is-active --quiet NetworkManager; then
    echo -e "${GREEN}Using NetworkManager...${NC}"
    
    # Backup NetworkManager connections
    if [[ -d /etc/NetworkManager/system-connections ]]; then
        cp -r /etc/NetworkManager/system-connections "$BACKUP_DIR/"
    fi
    
    # Get connection name
    CONNECTION_NAME=$(nmcli -t -f NAME,DEVICE connection show --active | grep "$ACTIVE_INTERFACE" | cut -d: -f1 | head -n1)
    
    if [[ -z "$CONNECTION_NAME" ]]; then
        CONNECTION_NAME="$ACTIVE_INTERFACE"
    fi
    
    echo -e "${YELLOW}Configuring connection: $CONNECTION_NAME${NC}"
    
    # Configure static IP - CRITICAL: Set all parameters in single command before method=manual
    # This prevents "ipv4.addresses: this property cannot be empty for 'method=manual'" error
    nmcli connection modify "$CONNECTION_NAME" \
        ipv4.addresses "$STATIC_IP/$PREFIX" \
        ipv4.gateway "$GATEWAY" \
        ipv4.dns "$DNS1 $DNS2" \
        ipv4.method manual \
        ipv4.ignore-auto-dns yes
    
    # Restart connection
    echo -e "${YELLOW}Restarting network connection...${NC}"
    nmcli connection down "$CONNECTION_NAME" 2>/dev/null || true
    sleep 2
    nmcli connection up "$CONNECTION_NAME"
    
    echo -e "${GREEN}✓ NetworkManager configuration applied${NC}"
    
elif systemctl is-active --quiet dhcpcd; then
    echo -e "${GREEN}Using dhcpcd (Raspberry Pi)...${NC}"
    
    # Backup dhcpcd.conf
    cp /etc/dhcpcd.conf "$BACKUP_DIR/dhcpcd.conf.backup"
    
    # Remove existing static configuration for this interface
    sed -i "/^interface $ACTIVE_INTERFACE/,/^$/d" /etc/dhcpcd.conf
    
    # Add new static configuration
    cat >> /etc/dhcpcd.conf <<EOF

# Static IP configuration for Distributed Robot System
# Added by setup_static_ip.sh on $(date)
interface $ACTIVE_INTERFACE
static ip_address=$STATIC_IP/$PREFIX
static routers=$GATEWAY
static domain_name_servers=$DNS1 $DNS2

# Fallback to DHCP if static fails
profile static_$ACTIVE_INTERFACE
static ip_address=$STATIC_IP/$PREFIX
static routers=$GATEWAY
static domain_name_servers=$DNS1 $DNS2

profile dhcp_fallback_$ACTIVE_INTERFACE
EOF
    
    # Restart dhcpcd
    systemctl restart dhcpcd
    
    echo -e "${GREEN}✓ dhcpcd configuration applied${NC}"
    
else
    echo -e "${YELLOW}Using /etc/network/interfaces...${NC}"
    
    # Backup interfaces file
    cp /etc/network/interfaces "$BACKUP_DIR/interfaces.backup"
    
    # Remove existing configuration for this interface
    sed -i "/^auto $ACTIVE_INTERFACE/,/^$/d" /etc/network/interfaces
    sed -i "/^iface $ACTIVE_INTERFACE/,/^$/d" /etc/network/interfaces
    
    # Add new static configuration
    cat >> /etc/network/interfaces <<EOF

# Static IP configuration for Distributed Robot System
# Added by setup_static_ip.sh on $(date)
auto $ACTIVE_INTERFACE
iface $ACTIVE_INTERFACE inet static
    address $STATIC_IP
    netmask 255.255.255.0
    gateway $GATEWAY
    dns-nameservers $DNS1 $DNS2
EOF
    
    # Restart networking
    ifdown "$ACTIVE_INTERFACE" 2>/dev/null || true
    sleep 2
    ifup "$ACTIVE_INTERFACE"
    
    echo -e "${GREEN}✓ /etc/network/interfaces configuration applied${NC}"
fi

echo ""
echo -e "${YELLOW}Verifying configuration...${NC}"
sleep 3

# Verify new IP
NEW_IP=$(ip -4 addr show "$ACTIVE_INTERFACE" | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

if [[ "$NEW_IP" == "$STATIC_IP" ]]; then
    echo -e "${GREEN}✓ Static IP successfully configured: $NEW_IP${NC}"
else
    echo -e "${RED}✗ Warning: IP address is $NEW_IP, expected $STATIC_IP${NC}"
    echo -e "${YELLOW}Configuration may take effect after reboot.${NC}"
fi

# Test gateway connectivity
echo ""
echo -e "${YELLOW}Testing gateway connectivity...${NC}"
if ping -c 2 -W 3 "$GATEWAY" &>/dev/null; then
    echo -e "${GREEN}✓ Gateway ($GATEWAY) is reachable${NC}"
else
    echo -e "${RED}✗ Warning: Cannot reach gateway ($GATEWAY)${NC}"
    echo -e "${YELLOW}Please check your router IP address.${NC}"
fi

# Test internet connectivity
echo -e "${YELLOW}Testing internet connectivity...${NC}"
if ping -c 2 -W 3 8.8.8.8 &>/dev/null; then
    echo -e "${GREEN}✓ Internet is accessible${NC}"
else
    echo -e "${RED}✗ Warning: Cannot reach internet${NC}"
    echo -e "${YELLOW}DNS or gateway configuration may need adjustment.${NC}"
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 Configuration Complete                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Backup saved to: $BACKUP_DIR${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Update ${GREEN}config/robot_config.yaml${NC} with:"
echo -e "     network:"
echo -e "       pc_ip: \"$([[ "$DEVICE_TYPE" == "pc" ]] && echo "$STATIC_IP" || echo "$OTHER_IP")\""
echo -e "       pi_ip: \"$([[ "$DEVICE_TYPE" == "pi" ]] && echo "$STATIC_IP" || echo "$OTHER_IP")\""
echo ""
echo -e "  2. Run this script on $OTHER_DEVICE with IP ${GREEN}$OTHER_IP${NC}"
echo ""
echo -e "  3. Test connectivity:"
echo -e "     ${GREEN}ping $OTHER_IP${NC}"
echo ""
echo -e "${YELLOW}To revert to DHCP:${NC}"
if systemctl is-active --quiet NetworkManager; then
    echo -e "  ${GREEN}sudo nmcli connection modify \"$CONNECTION_NAME\" ipv4.method auto${NC}"
    echo -e "  ${GREEN}sudo nmcli connection up \"$CONNECTION_NAME\"${NC}"
elif systemctl is-active --quiet dhcpcd; then
    echo -e "  ${GREEN}sudo cp $BACKUP_DIR/dhcpcd.conf.backup /etc/dhcpcd.conf${NC}"
    echo -e "  ${GREEN}sudo systemctl restart dhcpcd${NC}"
else
    echo -e "  ${GREEN}sudo cp $BACKUP_DIR/interfaces.backup /etc/network/interfaces${NC}"
    echo -e "  ${GREEN}sudo systemctl restart networking${NC}"
fi
echo ""
echo -e "${GREEN}✓ Setup complete! Your device will maintain this IP even when moved.${NC}"
