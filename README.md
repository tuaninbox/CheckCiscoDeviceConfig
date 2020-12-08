# CheckCiscoDeviceConfig
## Installation

pip install -r requirements

## Format of device list file -l:

Name,Host,Username,Password,Enable,Group
ASR,10.10.10.1,,,,WANRouter
7000,10.10.10.2,,,,WANRouter
7001,10.10.10.3,,,,WANRouter

## usage: getconfig.py [-h] [-f] -l  [-s] [-w] [-c  | -i]

Get Configuration

optional arguments:
  -h, --help         show this help message and exit
  -f , --find        Keyword to find
  -l , --list        Device List File
  -s , --site        Site to run command
  -w , --writefile   Write to File
  -c , --command     Command to run
  -i, --interactive  Interactive Session

## Some Example:

### 1. Interactive mode

python getconfig.py -l WANRouter.txt -s ASR -i
```
Command: show version
Cisco IOS XE Software, Version 03.10.04.S - Extended Support Release
Cisco IOS Software, ASR1000 Software (X86_64_LINUX_IOSD-UNIVERSALK9-M), Version 15.3(3)S4, RELEASE SOFTWARE (fc1)
Technical Support: http://www.cisco.com/techsupport
<omitted>
```
### 2. Command mode

python getconfig.py -l WANRouter.txt -s ASR -c "show version"
```
ASR - 10.10.10.1 Configuration:
Cisco IOS XE Software, Version 03.10.04.S - Extended Support Release
Cisco IOS Software, ASR1000 Software (X86_64_LINUX_IOSD-UNIVERSALK9-M), Version 15.3(3)S4, RELEASE SOFTWARE (fc1)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2014 by Cisco Systems, Inc.
<omitted>
```
### 3. Searching mode

python getconfig.py -l WANRouter.txt -s ASR -c "show access-list" -f "10.11.0.0"
```
ASR - 10.10.10.1: 10.11.0.0 in show access-list
```
### 4. Searching mode all sites

python getconfig.py -l WANRouter.txt -c "show access-list" -f "10.11.0.0"
```
ASR - 10.10.10.1: 10.11.0.0 in show access-list
7000 - 10.10.10.2: 10.11.0.0 in show access-list
7001 - 10.10.10.3: 10.11.0.0 in show access-list
```
### 5. Backup config

python getconfig.py -l WANRouter.txt -c "show run" -w Backup -s ASR
```
Configuration of site ASR - 10.10.10.1 saved in Backup/ASR.txt
```
### 6. Backup config for all sites

python getconfig.py -l WANRouter.txt -c "show run" -w Backup 
```
Configuration of site ASR - 10.10.10.1 saved in Backup/ASR.txt
Configuration of site 7000 - 10.10.10.2 saved in Backup/7000.txt
Configuration of site 7001 - 10.10.10.3 saved in Backup/7001.txt
```

