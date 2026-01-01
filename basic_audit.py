import pandas as pd
import re
import os

# --- Basic Configuration ---
CONFIG_FILE = 'config_file.txt'
# Using the exact name from your 'ls' command
CHECKLIST_FILE = 'CIS_Cisco_Router_WorkBench.xlsx' 
REPORT_NAME = 'Basic_Audit_Report2.txt'

def run_basic_audit():
    print("Step 1: Loading Configuration and Excel Checklist...")
    
    # Check if files exist before trying to open them
    if not os.path.exists(CONFIG_FILE) or not os.path.exists(CHECKLIST_FILE):
        print(f"Error: Make sure {CONFIG_FILE} and {CHECKLIST_FILE} are in this folder!")
        return

    # Load the config text
    with open(CONFIG_FILE, 'r') as f:
        config = f.read()
    
    # Load the checklist from EXCEL
    df = pd.read_excel(CHECKLIST_FILE)
    
    results = []
    print("Step 2: Running Regex matching engine...")

    for _, row in df.iterrows():
        # Using .get() to avoid errors if column names have spaces
        row_dict = row.to_dict()
        check_id = str(row_dict.get('S. No / CIS Control No', 'N/A'))
        check_point = str(row_dict.get('Check Point', 'Unknown'))
        
        status = "FAIL"
        remark = "Command not found"

        # --- Basic Regex Logic for Mentor Demo ---
        
        if "Version" in check_point:
            if re.search(r'^version \d+\.\d+', config, re.MULTILINE):
                status, remark = "PASS", "IOS version detected"

        elif "Hostname" in check_point:
            if re.search(r'^hostname \S+', config, re.MULTILINE):
                status, remark = "PASS", "Hostname is configured"

        elif "Password Encryption" in check_point:
            if "service password-encryption" in config:
                status, remark = "PASS", "Encryption is enabled"

        elif "SSH" in check_point:
            if "ip ssh version 2" in config:
                status, remark = "PASS", "SSHv2 is active"

        elif "AAA" in check_point:
            if "aaa new-model" in config:
                status, remark = "PASS", "AAA model enabled"
        
        else:
            status, remark = "MANUAL", "Requires human review"

        results.append({
            "ID": check_id,
            "Point": check_point,
            "Status": status,
            "Remark": remark
        })

    print(f"Step 3: Generating Text Report ({REPORT_NAME})...")
    
    with open(REPORT_NAME, 'w') as f:
        f.write("CIS CISCO ROUTER AUDIT - CORE LOGIC DEMO\n")
        f.write("="*60 + "\n")
        f.write(f"{'ID':<8} | {'STATUS':<8} | {'CHECK POINT':<25} | {'REMARK'}\n")
        f.write("-" * 80 + "\n")
        
        for res in results:
            f.write(f"{res['ID']:<8} | {res['Status']:<8} | {res['Point']:<25} | {res['Remark']}\n")

    print("\nSUCCESS: You can now show the 'Basic_Audit_Report.txt' file to your mentor.")

if __name__ == "__main__":
    run_basic_audit()