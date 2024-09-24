# GhostARP - Stealth ARP Spoofing Tool

```bash
                   ________.__                    __     _____ ____________________ 
                  /  _____/|  |__   ____  _______/  |_  /  _  \\______   \______   \
                 /   \  ___|  |  \ /  _ \/  ___/\   __\/  /_\  \|       _/|     ___/
                 \    \_\  \   Y  (  <_> )___ \  |  | /    |    \    |   \|    |    
                  \______  /___|  /\____/____  > |__| \____|__  /____|_  /|____|    
                         \/     \/           \/               \/       \/                    
                                ---- Stealth ARP Spoofing Tool ----
                 ===================================================================
                                𝕍𝕖𝕣𝕤𝕚𝕠𝕟 : 1.0     𝕋𝕨𝕚𝕥𝕥𝕖𝕣 : anishalx7        
                 ===================================================================    

``` 
## Overview

**GhostARP** is a powerful yet lightweight ARP spoofing tool, engineered for penetration testers, cybersecurity professionals, and ethical hackers. Designed with efficiency in mind, GhostARP allows users to conduct ARP spoofing attacks with minimal network disruption, enabling detailed traffic analysis and network vulnerability assessments.

By mimicking legitimate ARP packets, GhostARP allows you to reroute network traffic between the target and gateway, effectively performing **Man-in-the-Middle (MitM)** attacks. Whether for educational purposes or professional security assessments, GhostARP ensures the integrity of your tests by restoring ARP tables once the operation is terminated.

## Key Features

- **Stealth Mode**: Operates with minimal packet flooding to avoid detection.
- **User-Friendly**: Simple and intuitive command-line interface for quick usage.
- **Auto ARP Restoration**: Automatically resets ARP tables after interruption or shutdown.
- **Real-Time Packet Count**: Displays the number of spoofed packets sent during operation.
- **Customizable**: Easily adaptable for various network configurations and scenarios.
  
## Installation

### Requirements
Ensure the following dependencies are installed:
- Python 3.x
- Scapy (for crafting and sending ARP packets)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/anishalx/ghostarp.git
   cd ghostarp
   ```
   
2. Install the required dependencies:
   ```bash
   pip install scapy
   ```
   
3. Run the tool:
   ```bash
   python3 ghostarp.py
   ```

   ## Usage
