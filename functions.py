import meraki
import credentials

def ssid_firewall(dashboard, src_temp_id, dst_temp_id, dst_org_id):
    actions = []
    for n in range(15):
        l3_fw = dashboard.wireless.getNetworkWirelessSsidFirewallL3FirewallRules(networkId=src_temp_id, number=n)
        l7_fw = dashboard.wireless.getNetworkWirelessSsidFirewallL7FirewallRules(networkId=src_temp_id, number=n)

        indices = []
        for i in range(len(l3_fw['rules'])):
            if l3_fw['rules'][i]['comment'] == 'Wireless clients accessing LAN':
                indices.append(i)
                if l3_fw['rules'][i]['policy']=='deny':
                    l3_fw['allowLanAccess'] = False
            elif l3_fw['rules'][i]['comment'] == 'Default rule':
                indices.append(i)
        for item in sorted(indices, reverse=True):
            l3_fw['rules'].pop(item)

        a = {
            "resource": f"/networks/{dst_temp_id}/wireless/ssids/{n}/firewall/l7FirewallRules",
            "operation": "update",
            "body": {
                **l7_fw
            }
        }
        actions.append(a)
        dashboard.wireless.updateNetworkWirelessSsidFirewallL3FirewallRules(networkId=dst_temp_id, number=n, **l3_fw)

    dashboard.organizations.createOrganizationActionBatch(organizationId=dst_org_id, actions=actions,
                                                                     confirmed=True)

def ssid_shaping(dashboard, src_temp_id, dst_temp_id, dst_org_id):
    actions = []
    for i in range(15):
        shaping = dashboard.wireless.getNetworkWirelessSsidTrafficShapingRules(networkId=src_temp_id, number=i)
        a = {
            "resource": f"/networks/{dst_temp_id}/wireless/ssids/{i}/trafficShaping/rules",
            "operation": "update",
            "body": {
                **shaping
            }
        }
        actions.append(a)

    dashboard.organizations.createOrganizationActionBatch(organizationId=dst_org_id, actions=actions, confirmed=True)

def switch_qos(dashboard, src_temp_id, dst_temp_id, dst_org_id):
    src_qos = dashboard.switch.getNetworkSwitchQosRules(networkId=src_temp_id)
    dst_qos_order = dashboard.switch.getNetworkSwitchQosRulesOrder(networkId=dst_temp_id)
    actions = []
    # Delete all QoS rules in target template
    for item in dst_qos_order['ruleIds']:
        a = {
            "resource": f"/networks/{dst_temp_id}/switch/qosRules/{item}",
            "operation": "destroy",
            "body": {}
        }
        actions.append(a)
    # Create new QoS rules in target template matching source template
    for item in src_qos:
        # Remove source port and destination port from payload if set to None/Nay
        # Handle exception where source/destination is a range, not individual port
        try:
            if item['srcPort'] == None and item['protocol'] != 'ANY':
                del item['srcPort']
        except KeyError:
            print('Source port is a range')
            pass
        try:
            if item['dstPort'] == None and item['protocol'] != 'ANY':
                del item['dstPort']
        except KeyError:
            print('Destination port is a range')
            pass

        a = {
            "resource": f"/networks/{dst_temp_id}/switch/qosRules",
            "operation": "create",
            "body": {
                **item
            }
        }
        actions.append(a)

    # Split actions in chunks of 20 to send synchronous batches and keep QoS Rule order
    batches = [actions[x:x + 20] for x in range(0, len(actions), 20)]

    # Create one synchronous action batch for every batch in batches
    for batch in batches:
        dashboard.organizations.createOrganizationActionBatch(organizationId=dst_org_id, actions=batch, confirmed=True,
                                                              synchronous=True)
def switch_stp(dashboard, src_temp_id, src_org_id, dst_temp_id, dst_org_id):
    src_switch_profiles = dashboard.switch.getOrganizationConfigTemplateSwitchProfiles(
        organizationId=src_org_id, configTemplateId=src_temp_id)
    dst_switch_profiles = dashboard.switch.getOrganizationConfigTemplateSwitchProfiles(
        organizationId=dst_org_id, configTemplateId=dst_temp_id)

    src_switch_set = [item['model'] for item in src_switch_profiles]
    dst_switch_set = [item['model'] for item in dst_switch_profiles]

    if src_switch_set == dst_switch_set:
        src_stp = dashboard.switch.getNetworkSwitchStp(networkId=src_temp_id)
        payload = src_stp
        dst_stp = dashboard.switch.getNetworkSwitchStp(networkId=dst_temp_id)
        for i in range(len(src_stp['stpBridgePriority'])):
            for n in range(len(src_stp['stpBridgePriority'][i]['switchProfiles'])):
                for src_profile in src_switch_profiles:
                    if src_stp['stpBridgePriority'][i]['switchProfiles'][n] == src_profile['switchProfileId']:
                        for dst_profile in dst_switch_profiles:
                            if src_profile['model'] == dst_profile['model']:
                                src_stp['stpBridgePriority'][i]['switchProfiles'][n] = dst_profile['switchProfileId']
        dashboard.switch.updateNetworkSwitchStp(networkId=dst_temp_id, **src_stp)

def group_policies(dashboard, src_temp_id, dst_temp_id, dst_org_id):
    src_policies = dashboard.networks.getNetworkGroupPolicies(networkId=src_temp_id)
    dst_policies = dashboard.networks.getNetworkGroupPolicies(networkId=dst_temp_id)

    actions = []
    for policy in dst_policies:
        a = {
            "resource": f"/networks/{dst_temp_id}/groupPolicies/{policy['groupPolicyId']}",
            "operation": "destroy",
            "body": {}
        }
        actions.append(a)

    for policy in src_policies:
        dict = policy
        # Remove unneeded key from dict
        del dict['groupPolicyId']
        a = {
            "resource": f"/networks/{dst_temp_id}/groupPolicies",
            "operation": "create",
            "body": {
                **dict
            }
        }
        actions.append(a)

    # Split actions in chunks of 20 to send synchronous batches and destroy existing policies before creating new ones
    batches = [actions[x:x + 20] for x in range(0, len(actions), 20)]

    # Create one synchronous action batch for every batch in batches
    for batch in batches:
        dashboard.organizations.createOrganizationActionBatch(organizationId=dst_org_id, actions=batch, confirmed=True,
                                                              synchronous=True)

def net_alerts(dashboard, src_temp_id, dst_temp_id):
    src_alerts = dashboard.networks.getNetworkAlertsSettings(networkId=src_temp_id)
    dst_alerts = dashboard.networks.getNetworkAlertsSettings(networkId=dst_temp_id)

    for i in range(len(dst_alerts['alerts'])):
        for src_alert in src_alerts['alerts']:
            if dst_alerts['alerts'][i]['type'] == src_alert['type']:
                if src_alert != dst_alerts['alerts'][i]:
                    dst_alerts['alerts'][i] = src_alert

    # Remove clientConnectivity alerts, as they give issues when updating
    for i in range(len(dst_alerts['alerts'])):
        if dst_alerts['alerts'][i]['type'] == 'clientConnectivity':
            p = i

    dst_alerts['alerts'].pop(p)
    dashboard.networks.updateNetworkAlertsSettings(networkId=dst_temp_id, **dst_alerts)

def net_syslog(dashboard, src_temp_id, dst_temp_id):
    src_syslog = dashboard.networks.getNetworkSyslogServers(networkId=src_temp_id)
    dashboard.networks.updateNetworkSyslogServers(networkId=dst_temp_id, servers=src_syslog['servers'])

def net_snmp(dashboard, src_temp_id, dst_temp_id):
    src_snmp = dashboard.networks.getNetworkSnmp(networkId=src_temp_id)
    dashboard.networks.updateNetworkSnmp(networkId=dst_temp_id, **src_snmp)

def net_analytics(dashboard, src_temp_id, dst_temp_id):
    src_ta = dashboard.networks.getNetworkTrafficAnalysis(networkId=src_temp_id)
    dashboard.networks.updateNetworkTrafficAnalysis(networkId=dst_temp_id, **src_ta)
