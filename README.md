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
- colorama library

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/anishalx/ghostarp.git
   cd ghostarp
   ```
   
2. Install the required dependencies:
   ```bash
   pip install scapy colorama
   ```
   
3. Run the tool:
   ```bash
   python ghostarp.py
   ```

   ## Usage
   After installation, GhostARP can be executed from the terminal. The tool will prompt you for the Target IP and Gateway IP to initiate the ARP spoofing process.

1. **Run the Tool**

   Execute the script with the following command:

   ```bash
   python ghostarp.py
   ```
2. **Input Required Information**
   
    - You will be prompted to enter the target IP address.
    - Enter the IP address of the gateway.

Ensure that both IPs are valid and reachable on your network.

3. **Start Spoofing**
   
   The tool will start sending spoofed ARP packets. You will see the count of packets sent in real-time.

4. **Stopping the Tool**
   
   To stop the tool, press Ctrl + C. The tool will automatically restore the ARP tables for both the target and the gateway.
   


   ### Example Output
<b>DEMO VIDEO </b>
 <a href="https://www.youtube.com/@Alxhacks" target="_blank">
    <img src="https://raw.githubusercontent.com/maurodesouza/profile-readme-generator/master/src/assets/icons/social/youtube/default.svg" width="32" height="25" alt="youtube logo"  />
  </a>
  
  <p align="center"><img src="https://www.imghost.net/ib/msgDOsa85O9jeOX_1727550519.png" width="50%" height="20%"/></p> 

**Target machine**
  
  <p align="center"><img src="https://www.imghost.net/ib/66TVSvgknGryKpW_1727550982.png"" width="50%" height="20%"/></p> 


  
### Need Help?
For a detailed list of options and usage instructions, simply run:
```bash
python ghostarp.py -h
```
## Operating Systems

GhostARP is compatible with:

- **Windows**: Use Command Prompt or PowerShell.
- **macOS**: Utilize Terminal for seamless execution.
- **Linux**: Run in any terminal emulator of your choice.

## Important Notes
- Ethical Use: This tool should only be used in environments where you have permission to test. Unauthorized use on networks can lead to legal consequences.
  
- Network Impact: ARP spoofing can disrupt network operations; ensure you conduct tests in controlled environments.
## Contributing

We welcome contributions from the community! If you have ideas for improvements or new features, please follow these steps:

1. **Fork the repository**.
2. **Create a new branch** (`git checkout -b feature/YourFeature`).
3. **Make your changes** and commit them (`git commit -m 'Add some feature'`).
4. **Push your branch** (`git push origin feature/YourFeature`).
5. **Open a pull request**.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Special thanks to [Scapy](https://scapy.readthedocs.io/en/latest/) for powering this tool.
- Inspired by various network scanning tools and the open-source community.
