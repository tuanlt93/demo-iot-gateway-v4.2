from hmi.network import Network_Manager

print(Network_Manager.getWifiSSID())
print(Network_Manager.getConnectionIp("eth0"))
print(Network_Manager.getConnectionIp("wlan0"))
print(Network_Manager.getGateway("eth0"))
print(Network_Manager.getGateway("wlan0"))
print("SOMETHING")