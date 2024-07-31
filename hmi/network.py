import subprocess, re

class Ip_Parser:
    PATTERN = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:/(\d{1,2}))?$'

    @staticmethod
    def isIpv4(ip: str):
        return re.match(Ip_Parser.PATTERN, ip) is not None
    
    @staticmethod
    def parse(ip: str):
        match = re.match(Ip_Parser.PATTERN, ip)
        
        if match:
            return list(map(int, match.group(1).split('.')))
        return None

class Network_Manager:
    @staticmethod
    def terminal(cmd: list):
        try:
            # Run the iwgetid command to get the SSID
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout
            else:
                return None
        except Exception as e:
            print(e)
            return None
    
    @staticmethod
    def getWifiSSID():
        data = Network_Manager.terminal(["iwgetid -r"])
        if data:
            return data.strip()
        return None
    
    @staticmethod
    def getConnectionIp(device: str):
        """
        ip addr show <device> | grep -Po 'inet \K[\d.]+'
        """
        data = Network_Manager.terminal(f"ip addr show {device} | grep -Po 'inet \K[\d.]+'")
        
        if data:
            data = data.strip()
            return data
        else:
            return None
    
    @staticmethod
    def getGateway(device: str):
        """
        ip route show 0.0.0.0/0 dev <device> | cut -d\  -f3
        """
        data = Network_Manager.terminal(f"ip route show 0.0.0.0/0 dev {device} | cut -d\  -f3")
        
        if data:
            data = data.strip()
            return data
        else:
            return None