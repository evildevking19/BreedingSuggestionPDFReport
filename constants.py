import os, math
from collections import defaultdict
from PyQt5.QtWidgets import QMessageBox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

MSG_SUCCESS = 0
MSG_WARNING = 1
MSG_ERROR = -1

scores = {}
def getGoogleSheetService():
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    # credential = None
    # if os.path.exists('assets/utils/token.json'):
    #     credential = Credentials.from_authorized_user_file('assets/utils/token.json', SCOPES)
    # if not credential or not credential.valid:
    #     if credential and credential.expired and credential.refresh_token:
    #         credential.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file('assets/utils/credentials.json', SCOPES)
    #         credential = flow.run_local_server(port=0)
    #     with open('assets/utils/token.json', 'w') as token:
    #         token.write(credential.to_json())
    # try:
    #     service = build("sheets", "v4", credentials=credential)
    #     return service
    # except HttpError as err:
    #     print(err)
    #     return None
    
def getGoogleDriver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source":
            "const newProto = navigator.__proto__;"
            "delete newProto.webdriver;"
            "navigator.__proto__ = newProto;"
    })
    return driver
    
def load_spreadsheet_data(wsheetId, msheetId):
    worksheet = getGoogleSheetService().spreadsheets()
    sheet_names = []
    try:
        wsheet_metadata = worksheet.get(spreadsheetId=wsheetId).execute()
        for sheet in wsheet_metadata['sheets']:
            sheet_names.append(sheet['properties']['title'])
        try:
            worksheet.get(spreadsheetId=msheetId).execute()
            return {"status": MSG_SUCCESS, "msg": "Success", "data": sheet_names}
        except:
            return {"status": MSG_ERROR, "msg": "The Google Sheet Service is not able to use for now. Try again later."}
    except:
        return {"status": MSG_ERROR, "msg": "The Google Sheet Service is not able to use for now. Try again later."}
    
def getSheetColumnLabels(start_index, n):
    column_labels = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
    sheet_column_labels = []

    for i in range(start_index, n):
        if i < len(column_labels):
            sheet_column_labels.append(column_labels[i])
        else:
            # If you need more than 26 columns, you can extend the labels with combinations like AA, AB, etc.
            div, mod = divmod(i, len(column_labels))
            label = column_labels[mod]
            while div > 0:
                div, mod = divmod(div - 1, len(column_labels))
                label = column_labels[mod] + label
            sheet_column_labels.append(label)

    return sheet_column_labels
        
def getColumnLabelByIndex(ind):
    labels = getSheetColumnLabels(0, 50)
    return labels[ind]

def getProjectPath():
    return os.getcwd().replace("\\", "/")

def getTextValue(list, index):
    try:
        return list[index].find_element(By.CSS_SELECTOR, "div.block-name").get_attribute("title")
    except:
        return ""

def getPedigreeDataFromTable(table, version):
    result = []
    ## Extract the values will be input in spreadsheet ##
    ids = ["MMM", "MMMM", "MM", "MMF", "MMFM", "M", "MFM", "MFMM", "MF", "MFF", "MFFM", "FMM", "FMMM", "FM", "FMF", "FMFM", "F", "FFM", "FFMM", "FF", "FFF", "FFFM"]
    for id in ids:
        td_elem = table.find_element(By.CSS_SELECTOR, f"td#{id}")
        next_td_elem = table.find_element(By.CSS_SELECTOR, f"td#{id} + td")
        if next_td_elem.get_attribute("class") == "pedigree-cell-highlight":
            label = td_elem.find_element(By.CSS_SELECTOR, "div.block-name").get_attribute("title").title()
            if version == 2:
                label += "*"
            result.append(label)
        else:
            result.append(td_elem.find_element(By.CSS_SELECTOR, "div.block-name").get_attribute("title").title())

    return result

def getGradeInfo(g_sire, g_damssire, g_damssire2, g_damssire3):
    tempbar_obj = {"B-": 657, "B": 693, "A-": 730, "A": 760, "A+": 792, "A*": 832}
    letter_grade_constants = {"A+": 5, "A": 4, "A-": 3, "B": 2, "B-": 1}
    sum_grades = (letter_grade_constants[g_sire] if g_sire != None else 0) + (letter_grade_constants[g_damssire] if g_damssire != None else 0) + (letter_grade_constants[g_damssire2] if g_damssire2 != None else 0) + letter_grade_constants[g_damssire3]
    avg_grade_value = float(get2DigitsStringValue(float(sum_grades / 4)))
    final_grade_value = math.ceil(avg_grade_value)
    if final_grade_value >= 5:
        return {"letter": "A+", "color_info": [36, 246, 0], "tempbar_pos": getPositionByPercent(tempbar_obj["A+"], tempbar_obj["A*"], 50)}
    elif final_grade_value == 4:
        remaining_val = 4- avg_grade_value
        if remaining_val == 0:
            return {"letter": "A", "color_info": [152, 245, 0], "tempbar_pos": tempbar_obj["A"]}
        else:
            return {"letter": "A", "color_info": [152, 245, 0], "tempbar_pos": getPositionByPercent(tempbar_obj["A"], tempbar_obj["A+"], remaining_val*100)}
    elif final_grade_value == 3:
        remaining_val = 3 - avg_grade_value
        if remaining_val == 0:
            return {"letter": "A-", "color_info": [245, 246, 0], "tempbar_pos": tempbar_obj["A-"]}
        else:
            return {"letter": "A-", "color_info": [245, 246, 0], "tempbar_pos": getPositionByPercent(tempbar_obj["A-"], tempbar_obj["A"], remaining_val*100)}
    elif final_grade_value == 2:
        remaining_val = 2 - avg_grade_value
        if remaining_val == 0:
            return {"letter": "B", "color_info": [237, 158, 0], "tempbar_pos": tempbar_obj["B"]}
        else:
            return {"letter": "B", "color_info": [237, 158, 0], "tempbar_pos": getPositionByPercent(tempbar_obj["B"], tempbar_obj["A-"], remaining_val*100)}
    elif final_grade_value == 1:
        remaining_val = 1 - avg_grade_value
        if remaining_val == 0:
            return {"letter": "B-", "color_info": [255, 1, 1], "tempbar_pos": tempbar_obj["B-"]}
        else:
            return {"letter": "B-", "color_info": [255, 1, 1], "tempbar_pos": getPositionByPercent(tempbar_obj["B-"], tempbar_obj["B"], remaining_val*100)}
    
def get2DigitsStringValue(input):
    return '%.2f' % float(input)

def getPositionByPercent(fval, sval, percent):
    diff = sval - fval
    result = int((percent / 100) * diff)
    return fval + result

def groupBySireAndCountHorse(init_data, oned_data, genType):
    result_dict = defaultdict(lambda: defaultdict(int))
    
    for h, s in init_data:
        result_dict[s.title()][h.title()] += 1
    result_array = []
    for s, h_cnts in result_dict.items():
        for h, cnt in h_cnts.items():
            result_array.append([h, s, str(cnt), ""])
    
    tmp = result_array
    for i, v in enumerate(tmp):
        sum = 0
        for d in oned_data:
            if d[0].lower() == v[0].lower():
                if len(d) > 19 and d[19] != "":
                    sum += float(d[19].lstrip("$").replace(",",""))
                else:
                    sum += 0
        result_array[i][3] = f"${float(sum):,.2f}" if sum != 0 else ""
    return sortByIndex2(result_array, 2, genType)

def sortByRate(arr, genType):
    sorted_arr = sorted(arr, key=lambda x: custom_key(x, 1), reverse=True)
    if genType == 0:
        cutted_arr = sorted_arr[:10]
        last_element = cutted_arr[-1]
        for v in sorted_arr[10:]:
            if v[1] == last_element[1]:
                cutted_arr.append(v)
            else: break
        return cutted_arr
    else:
        return sorted_arr

def sortByCoi(arr, genType):
    sorted_arr = sorted(arr, key=lambda x: float(x[4][:-1]), reverse=True)
    if genType == 0:
        cutted_arr = sorted_arr[:10]
        last_element = cutted_arr[-1]
        for v in sorted_arr[10:]:
            if v[4] == last_element[4]:
                cutted_arr.append(v)
            else: break
        filtered_arr = [x for x in cutted_arr if x[4].strip() != "0.00%"]
        if len(filtered_arr) == 0:
            return sortByVariant(cutted_arr, genType)
        else:
            return filtered_arr
    else:
        return sorted_arr
    
def sortByCoi2(arr):
    return sorted(arr, key=lambda x: float(x[5][:-1]), reverse=True)
    
def sortByCoiForUnrated(arr, genType):
    sorted_arr = sorted(arr, key=lambda x: float(x[4][:-1]), reverse=True)
    if genType == 0:
        cutted_arr = sorted_arr[:10]
        last_element = cutted_arr[-1]
        for v in sorted_arr[10:]:
            if v[4] == last_element[4]:
                cutted_arr.append(v)
            else: break
        filtered_arr = [x for x in cutted_arr if x[4].strip() != "0.00%"]
        if len(filtered_arr) == 0:
            return sortByVariant(cutted_arr, genType)
        else:
            return cutted_arr
    else:
        return sorted_arr

def sortByVariant(arr, genType):
    sorted_arr = sorted(arr, key=lambda x: custom_key(x, 2), reverse=True)
    if genType == 0:
        cutted_arr = sorted_arr[:10]
        last_element = cutted_arr[-1]
        for v in sorted_arr[10:]:
            if v[2] == last_element[2]:
                cutted_arr.append(v)
            else: break
        return cutted_arr
    else:
        return sorted_arr
    
def sortByVariant2(arr):
    return sorted(arr, key=lambda x: custom_key(x, 3), reverse=True)
    
def sortByIndex(arr, ind):
    sorted_arr = sorted(arr, key=lambda x: float(x[ind]), reverse=True)
    cutted_arr = sorted_arr[:10]
    last_element = cutted_arr[-1]
    for v in sorted_arr[10:]:
        if v[ind] == last_element[ind]:
            cutted_arr.append(v)
        else: break
    return cutted_arr

def sortByIndex2(arr, ind, genType):
    sorted_arr = sorted(arr, key=lambda x: float(x[ind]), reverse=True)
    if genType == 0:
        cutted_arr = sorted_arr[:10]
        last_element = cutted_arr[-1]
        for v in sorted_arr[10:]:
            if v[ind] == last_element[ind]:
                cutted_arr.append(v)
            else: break
        return cutted_arr
    else:
        return sorted_arr
    
def rearrangeByOtherTiers(arr, genType):
    obj = {"3": [], "2": [], "1": [], "0": []}
    for row in arr:
        if row[0] == "":
            obj["0"].append(row)
        elif len(row[0].split(",")) == 3:
            obj["3"].append(row)
        elif len(row[0].split(",")) == 2:
            obj["2"].append(row)
        elif len(row[0].split(",")) == 1:
            obj["1"].append(row)
    result_arr = sortByVariant2(obj["3"]) + sortByVariant2(obj["2"]) + sortByVariant2(obj["1"]) + sortByVariant2(obj["0"])
    if genType == 0:
        cutted_arr = result_arr[:10]
        last_element = cutted_arr[-1]
        for v in result_arr[10:]:
            if v[2] == last_element[2]:
                cutted_arr.append(v)
            else: break
        return cutted_arr
    else:
        return result_arr

def custom_key(item, ind):
    if item[ind] == "N/A":
        return float('0')
    elif item[ind] == "" or item[ind].replace("%", "") == "":
        return float('0')
    else:
        return float(item[ind].replace("%",""))
    
def getJsonDataOfStallion(data):
    jsonObj = {}
    jsonObj["name"] = data[0]

    jsonObj["s"] = {}
    jsonObj["s"]["name"] = data[1]
    jsonObj["s"]["s"] = {}
    jsonObj["s"]["s"]["name"] = data[3]
    jsonObj["s"]["s"]["s"] = {}
    jsonObj["s"]["s"]["s"]["name"] = data[7]
    jsonObj["s"]["s"]["d"] = {}
    jsonObj["s"]["s"]["d"]["name"] = data[8]
    jsonObj["s"]["s"]["d"]["s"] = {}
    jsonObj["s"]["s"]["d"]["s"]["name"] = data[17]
    jsonObj["s"]["s"]["d"]["d"] = {}
    jsonObj["s"]["s"]["d"]["d"]["name"] = data[18]
    jsonObj["s"]["s"]["s"]["s"] = {}
    jsonObj["s"]["s"]["s"]["s"]["name"] = data[15]
    jsonObj["s"]["s"]["s"]["d"] = {}
    jsonObj["s"]["s"]["s"]["d"]["name"] = data[16]
    jsonObj["s"]["d"] = {}
    jsonObj["s"]["d"]["name"] = data[4]
    jsonObj["s"]["d"]["s"] = {}
    jsonObj["s"]["d"]["s"]["name"] = data[9]
    jsonObj["s"]["d"]["d"] = {}
    jsonObj["s"]["d"]["d"]["name"] = data[10]
    jsonObj["s"]["d"]["s"]["s"] = {}
    jsonObj["s"]["d"]["s"]["s"]["name"] = data[19]
    jsonObj["s"]["d"]["s"]["d"] = {}
    jsonObj["s"]["d"]["s"]["d"]["name"] = data[20]
    jsonObj["s"]["d"]["d"]["s"] = {}
    jsonObj["s"]["d"]["d"]["s"]["name"] = data[21]
    jsonObj["s"]["d"]["d"]["d"] = {}
    jsonObj["s"]["d"]["d"]["d"]["name"] = data[22]

    jsonObj["d"] = {}
    jsonObj["d"]["name"] = data[2]
    jsonObj["d"]["s"] = {}
    jsonObj["d"]["s"]["name"] = data[5]
    jsonObj["d"]["s"]["s"] = {}
    jsonObj["d"]["s"]["s"]["name"] = data[11]
    jsonObj["d"]["s"]["d"] = {}
    jsonObj["d"]["s"]["d"]["name"] = data[12]
    jsonObj["d"]["s"]["s"]["s"] = {}
    jsonObj["d"]["s"]["s"]["s"]["name"] = data[23]
    jsonObj["d"]["s"]["s"]["d"] = {}
    jsonObj["d"]["s"]["s"]["d"]["name"] = data[24]
    jsonObj["d"]["s"]["d"]["s"] = {}
    jsonObj["d"]["s"]["d"]["s"]["name"] = data[25]
    jsonObj["d"]["s"]["d"]["d"] = {}
    jsonObj["d"]["s"]["d"]["d"]["name"] = data[26]
    jsonObj["d"]["d"] = {}
    jsonObj["d"]["d"]["name"] = data[6]
    jsonObj["d"]["d"]["s"] = {}
    jsonObj["d"]["d"]["s"]["name"] = data[13]
    jsonObj["d"]["d"]["d"] = {}
    jsonObj["d"]["d"]["d"]["name"] = data[14]
    jsonObj["d"]["d"]["s"]["s"] = {}
    jsonObj["d"]["d"]["s"]["s"]["name"] = data[27]
    jsonObj["d"]["d"]["s"]["d"] = {}
    jsonObj["d"]["d"]["s"]["d"]["name"] = data[28]
    jsonObj["d"]["d"]["d"]["s"] = {}
    jsonObj["d"]["d"]["d"]["s"]["name"] = data[29]
    jsonObj["d"]["d"]["d"]["d"] = {}
    jsonObj["d"]["d"]["d"]["d"]["name"] = data[30]

    return jsonObj

def showMessageBox(message, msg_type):
    msg = QMessageBox()
    if msg_type == MSG_ERROR:
        msg.setIcon(QMessageBox.Critical)
    elif msg_type == MSG_WARNING:
        msg.setIcon(QMessageBox.Warning)
    elif msg_type == MSG_SUCCESS:
        msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("Message")
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()