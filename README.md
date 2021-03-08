# meraki-crossorg-templates

![image alt text](./diagram.png)

This is a simple application that can clone switch and SSID settings from one template in one source organization to another template in a target organization. The use case is for customers who have very large (over 25000 switches and APs) but very simple deployments, like elementary schools.

**How to use:**
1. Run pip install -r requirements.txt
2. Add your Meraki API key to the credentials.py file between the quotation marks
3. Make sure this API key has write access to both the source and target organization
4. Run the script with python main.py
5. Select your source and target templates
6. Check the boxes for copying SSIDs and/or switch ports

![image alt text](./image_crossorg_app.png)

**Current capabilities:**
1. Clone SSIDs
2. Clone SSID Firewalls
3. Clone SSID Traffic Shaping
4. Clone Switch Profile Ports
5. Clone Switch QoS
6. Clone Switch STP
7. Clone Network Group Policies
8. Clone Network Alerts
9. Clone Network Traffic Analytics
10. Clone Network Syslog
11. Clone Network SNMP

**Caveats:**
1. For copying switch settings, both the source and target templates must have switch profiles created for the same switch models
2. The profiles themselves can be empty of configurations, but they have to exist before running the script
3. It is highly recommended that you test this in a test template before running in a production template
