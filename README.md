# CheckCiscoDeviceConfig
usage: getconfig.py [-h] [-f] -l  [-s] [-w] [-c  | -i]

Get Configuration

optional arguments:
  -h, --help         show this help message and exit
  -f , --find        Keyword to find
  -l , --list        Device List File
  -s , --site        Site to run command
  -w , --writefile   Write to File
  -c , --command     Command to run
  -i, --interactive  Interactive Session

  Format of device list file -l:
Name,Host,Username,Password,Enable,Group
ASR,10.10.10.1,,,,WANRouter
7000,10.10.10.2,,,,WANRouter
7001,10.10.10.3,,,,WANRouter