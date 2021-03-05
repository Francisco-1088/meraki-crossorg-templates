# meraki-crossorg-templates
This is a simple application that can clone switch and SSID settings from one template in one source organization to another template in a target organization. The use case is for customers who have very large (over 25000 switches and APs) but very simple deployments, like elementary schools.

How to use:
1. Run pip install -r requirements.txt
2. Add your Meraki API key to the credentials.py file between the quotation marks
3. Make sure this API key has write access to both the source and target organization
4. Run the script with python main.py
5. Select your source and target templates
6. Check the boxes for copying SSIDs and/or switch ports
