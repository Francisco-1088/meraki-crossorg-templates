import meraki
import PySimpleGUI as sg
import credentials
import functions

def gather_templates(api_client):

    orgs = api_client.organizations.getOrganizations()
    temps = []
    non_api = []
    j = 0
    for org in orgs:
        try:
            temp = dashboard.organizations.getOrganizationConfigTemplates(organizationId=org['id'])
            temps.append(temp)
            j = j + 1
        except meraki.APIError as e:
            print(e)
            temps.append(j)
            non_api.append(j)
            j = j + 1
    org_templates = []

    for i in range(len(orgs)):
        if i in non_api:
            continue
        else:
            dict = orgs[i]
            dict['templates'] = temps[i]
            org_templates.append(dict)

    return org_templates

def open_window(message, lines=4, width=20):
    layout = [
        [sg.Text(
            f'{message}',
            size=(width, lines), font=('Any', 16), text_color='#1c86ee',
            justification='center')],
        # [sg.Image(data=imgbytes, key='_IMAGE_')],
        [sg.Exit()]
    ]
    win = sg.Window('Meraki Cross-Org Templates',
                    default_element_size=(14, 1),
                    text_justification='right',
                    auto_size_text=False,
                    font=('Helvetica', 20)).Layout(layout)
    win.Read()

if __name__ == "__main__":
    dashboard = meraki.DashboardAPI(api_key=credentials.api_key)
    org_templates = gather_templates(dashboard)
    org_temp_list = []
    for org in org_templates:
        for temp in org['templates']:
            item = {'name': org['name']+' - '+ temp['name'], 'id':temp['id'], 'org_id': org['id'], 'prodTypes':temp['productTypes']}
            org_temp_list.append(item)

    sg.ChangeLookAndFeel('LightGreen')
    layout = [
        [sg.Text('Meraki Cross Org Templates', size=(19, 1), font=('Any', 18), text_color='#1c86ee',
                 justification='center')],
        [sg.Text('Source Template  '), sg.Combo([temp['name'] for temp in org_temp_list], key='_SRC_TMP_')],
        [sg.Text('Target Template  '), sg.Combo([temp['name'] for temp in org_temp_list], key='_DST_TMP_')],
        [sg.Text(' ' * 8), sg.Checkbox('Clone Wireless - SSIDs', key='_SSID_', size=(40,1))],
        [sg.Text(' ' * 8), sg.Checkbox('Clone Wireless - SSID Firewall', key='_FW_', size=(40, 1))],
        [sg.Text(' ' * 8), sg.Checkbox('Clone Wireless - SSID Traffic Shaping', key="_SHAPE_", size=(40, 1))],
        [sg.Text(' ' * 8), sg.Checkbox('Clone Switch - Ports and Profiles', key="_PORT_PRF_", size=(40, 1))],
        [sg.Text(' ' * 8), sg.Checkbox('Clone Switch - QoS Settings', key="_QOS_", size=(40, 1))],
        [sg.Text(' ' * 8), sg.Checkbox('Clone Switch - STP Settings', key="_STP_", size=(40, 1))],
        [sg.Text(' ' * 8), sg.Checkbox('Clone Network - Group Policies', key="_GP_", size=(40, 1))],
        [sg.Text(' ' * 8), sg.Checkbox('Clone Network - Alerts', key="_ALERT_", size=(40, 1))],
        [sg.Text(' ' * 8), sg.Checkbox('Clone Network - Syslog', key="_SYSLOG_", size=(40, 1))],
        [sg.Text(' ' * 8), sg.Checkbox('Clone Network - SNMP', key="_SNMP_", size=(40, 1))],
        [sg.Text(' ' * 8), sg.Checkbox('Clone Network - Traffic Analysis', key="_ANALYTICS_", size=(40, 1))],
        [sg.OK(), sg.Cancel()]
    ]

    win = sg.Window('Meraki Cross Org Templates',
                    default_element_size=(20, 1),
                    text_justification='right',
                    auto_size_text=False,
                    font=('Helvetica', 20)).Layout(layout)
    event, values = win.Read()
    if event is None or event == 'Cancel':
        exit()
    src_temp = values['_SRC_TMP_']
    dst_temp = values['_DST_TMP_']
    clone_ssids = values['_SSID_']
    clone_switch_profiles = values['_PORT_PRF_']
    clone_ssid_fw = values['_FW_']
    clone_ssid_ts = values['_SHAPE_']
    clone_switch_qos = values['_QOS_']
    clone_switch_stp = values['_STP_']
    clone_net_gps = values['_GP_']
    clone_net_alerts = values['_ALERT_']
    clone_net_syslog = values['_SYSLOG_']
    clone_net_snmp = values['_SNMP_']
    clone_net_ta = values['_ANALYTICS_']
    args = values

    win.Close()

    for i in range(len(org_temp_list)):
        if org_temp_list[i]['name']==src_temp:
            src_temp_id = org_temp_list[i]['id']
            src_org_id = org_temp_list[i]['org_id']
            src_temp_prods = org_temp_list[i]['prodTypes']
        if org_temp_list[i]['name']==dst_temp:
            dst_temp_id = org_temp_list[i]['id']
            dst_org_id = org_temp_list[i]['org_id']
            dst_temp_prods = org_temp_list[i]['prodTypes']

    win_started = False
    try:
        if clone_ssids:
            if 'wireless' not in src_temp_prods:
                error = 'Your source template does not have wireless products, so you cannot copy SSIDs from it.'
                open_window(error)
            elif 'wireless' not in dst_temp_prods:
                error = 'Your destination template does not have wireless products, so you cannot copy SSIDs to it.'
                open_window(error)
            else:
                try:
                    ssids = dashboard.wireless.getNetworkWirelessSsids(networkId=src_temp_id)
                    actions = []
                    for ssid in ssids:
                        d = ssid
                        upd = dict(d)
                        del upd['number']
                        a = {
                            "resource": f"/networks/{dst_temp_id}/wireless/ssids/{d['number']}",
                            "operation": "update",
                            "body": {
                                **upd
                            }
                        }
                        actions.append(a)
                    batch = dashboard.organizations.createOrganizationActionBatch(organizationId=dst_org_id,
                                                                                  actions=actions, confirmed=True)
                except meraki.APIError as e:
                    open_window(e)
        if clone_switch_profiles:
            if 'switch' not in src_temp_prods:
                error = 'Your source template does not have switch products, so you cannot copy ports from it.'
                open_window(error)
            elif 'switch' not in dst_temp_prods:
                error = 'Your destination template does not have switch products, so you cannot copy ports to it.'
                open_window(error)
            else:
                try:
                    src_switch_profiles = dashboard.switch.getOrganizationConfigTemplateSwitchProfiles(
                        organizationId=src_org_id, configTemplateId=src_temp_id)
                    dst_switch_profiles = dashboard.switch.getOrganizationConfigTemplateSwitchProfiles(
                        organizationId=dst_org_id, configTemplateId=dst_temp_id)

                    src_switch_set = [item['name'] for item in src_switch_profiles]
                    dst_switch_set = [item['name'] for item in dst_switch_profiles]

                    if set(src_switch_set) == set(dst_switch_set):
                        for profile in src_switch_profiles:
                            switch_profiles_ports = dashboard.switch.getOrganizationConfigTemplateSwitchProfilePorts(
                                organizationId=src_org_id, configTemplateId=src_temp_id,
                                profileId=profile['switchProfileId'])
                            for dst_profile in dst_switch_profiles:
                                if dst_profile['name']==profile['name']:
                                    actions = []
                                    for port in switch_profiles_ports:
                                        d = port
                                        upd = dict(d)
                                        del upd['portId']
                                        a = {
                                            "resource": f"/organizations/{dst_org_id}/configTemplates/{dst_temp_id}/switch/profiles/{dst_profile['switchProfileId']}/ports/{port['portId']}",
                                            "operation": "update",
                                            "body": {
                                                **upd
                                            }
                                        }
                                        actions.append(a)
                                    batch = dashboard.organizations.createOrganizationActionBatch(organizationId=dst_org_id,actions=actions, confirmed=True)

                    else:
                        error = f'Your source template has profiles for {src_switch_set}'
                        error = error + f'\nYour destination template has profiles for {dst_switch_set}'
                        error = error + '\n\nMake sure they are the same before running the config sync tool.'
                        print(error)
                        open_window(error,lines=8,width=45)
                except meraki.APIError as e:
                    open_window(e)
        if clone_ssid_fw:
            if 'wireless' not in src_temp_prods:
                error = 'Your source template does not have wireless products, so you cannot copy SSIDs from it.'
                open_window(error)
            elif 'wireless' not in dst_temp_prods:
                error = 'Your destination template does not have wireless products, so you cannot copy SSIDs to it.'
                open_window(error)
            else:
                try:
                    functions.ssid_firewall(dashboard=dashboard, src_temp_id=src_temp_id,dst_temp_id=dst_temp_id,dst_org_id=dst_org_id)
                except meraki.APIError as e:
                    open_window(e)
        if clone_ssid_ts:
            if 'wireless' not in src_temp_prods:
                error = 'Your source template does not have wireless products, so you cannot copy SSIDs from it.'
                open_window(error)
            elif 'wireless' not in dst_temp_prods:
                error = 'Your destination template does not have wireless products, so you cannot copy SSIDs to it.'
                open_window(error)
            else:
                try:
                    functions.ssid_shaping(dashboard=dashboard, src_temp_id=src_temp_id, dst_org_id=dst_org_id, dst_temp_id=dst_temp_id)
                except meraki.APIError as e:
                    open_window(e)
        if clone_switch_qos:
            if 'switch' not in src_temp_prods:
                error = 'Your source template does not have switch products, so you cannot copy ports from it.'
                open_window(error)
            elif 'switch' not in dst_temp_prods:
                error = 'Your destination template does not have switch products, so you cannot copy ports to it.'
                open_window(error)
            else:
                try:
                    functions.switch_qos(dashboard=dashboard, src_temp_id=src_temp_id, dst_temp_id=dst_temp_id,dst_org_id=dst_org_id)
                except meraki.APIError as e:
                    open_window(e)
        if clone_switch_stp:
            if 'switch' not in src_temp_prods:
                error = 'Your source template does not have switch products, so you cannot copy ports from it.'
                open_window(error)
            elif 'switch' not in dst_temp_prods:
                error = 'Your destination template does not have switch products, so you cannot copy ports to it.'
                open_window(error)
            else:
                try:
                    functions.switch_stp(dashboard=dashboard, src_temp_id=src_temp_id, src_org_id=src_org_id, dst_temp_id=dst_temp_id, dst_org_id=dst_org_id)
                except meraki.APIError as e:
                    open_window(e)
        if clone_net_gps:
            try:
                functions.group_policies(dashboard=dashboard,src_temp_id=src_temp_id,dst_temp_id=dst_temp_id, dst_org_id=dst_org_id)
            except meraki.APIError as e:
                open_window(e)
        if clone_net_alerts:
            try:
                functions.net_alerts(dashboard=dashboard, src_temp_id=src_temp_id, dst_temp_id=dst_temp_id)
            except meraki.APIError as e:
                open_window(e)
        if clone_net_syslog:
            try:
                functions.net_syslog(dashboard=dashboard, src_temp_id=src_temp_id, dst_temp_id=dst_temp_id)
            except meraki.APIError as e:
                open_window(e)
        if clone_net_snmp:
            try:
                functions.net_snmp(dashboard=dashboard, src_temp_id=src_temp_id, dst_temp_id=dst_temp_id)
            except meraki.APIError as e:
                open_window(e)
        if clone_net_ta:
            try:
                functions.net_analytics(dashboard=dashboard, src_temp_id=src_temp_id, dst_temp_id=dst_temp_id)
            except meraki.APIError as e:
                open_window(e)

        success = 'Your template was copied successfully!'
        open_window(success)
    except meraki.APIError as e:
        open_window(e)
