#!/usr/bin/python3
import banner
from banner.colors import *
from banner.colors import colorize

LEGAL_DISCLAIMER = "\n[!] Legal disclaimer: Usage of GhostARP for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws. Developer assumes no liability and is not responsible for any misuse or damage caused by this program."
LEGAL_DISCLAIMER = colorize(string=LEGAL_DISCLAIMER, color="white", normal=True)

# Styling for banner elements
I1 = colorize(string="'", color="yellow", normal=True, background="red")
I1 = f"{I1}{BRIGHT}{yellow}"
I2 = colorize(string='"', color="yellow", normal=True, background="red")
I2 = f"{I2}{BRIGHT}{yellow}"
I3 = colorize(string=")", color="yellow", normal=True, background="red")
I3 = f"{I3}{BRIGHT}{yellow}"

# Version, GitHub link, and Author info
VERSION = colorize(string="1.0.0", color="bright_yellow", bold=True)
START_BRACES = colorize(string="{", color="bright_white", normal=True)
END_BRACES = f'{colorize(string="}", color="bright_white", normal=True)}'
END_BRACES = f"{END_BRACES}{BRIGHT}{yellow}"
VERSION_STRING = f"{START_BRACES}{VERSION}{END_BRACES}"
GITHUB_URL = colorize(
    string="https://github.com/anishalx/ghostarp", color="bright_white", faint=True
)
by = colorize(string="Author:", color="bright_cyan", bold=True)
name = colorize(string="Anish", color="bright_green", bold=True)
name += colorize(string="@", color="bright_red", bold=True)
name += colorize(string="GhostARP", color="bright_cyan", bold=True)
desc = colorize(
    string="An advanced ARP spoofing and packet sniffing tool.",
    color="bright_green",
)
line = colorize(string="", color="green", bold=True)

# New banner for GhostARP
banner = """
                   ________.__                    __     _____ ____________________ 
                  /  _____/|  |__   ____  _______/  |_  /  _  \\______   \______   \\
                 /   \\  ___|  |  \\ /  _ \\/  ___/\\   __\\/  /_\\  \\|       _/|     ___/
                 \\    \\_\\  \\   Y  (  <_> )___ \\  |  | /    |    \\    |   \\|    |    
                  \\______  /___|  /\\____/____  > |__| \\____|__  /____|_  /|____|    
                         \\/     \\/           \\/               \\/       \\/                    
                                ---- Stealth ARP Spoofing Tool ----
                 ===================================================================
                                𝕍𝕖𝕣𝕤𝕚𝕠𝕟 : 1.0     𝕋𝕨𝕚𝕥𝕥𝕖𝕣 : anishalx7        
                 ===================================================================    

""" 

# Final banner print with colorization
BANNER = colorize(string=banner, color="yellow", bold=True)
print(BANNER)
print(LEGAL_DISCLAIMER)
