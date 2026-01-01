import pandas as pd
import re
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# --- FILENAMES ---
# These must match exactly what you saw in 'ls'
CONFIG_FILE = 'config_file.txt'
CHECKLIST_FILE = 'CIS_Cisco_Router_WorkBench.xlsx'

def generate_pdf(df, filename):
    """Generates a professional PDF report."""
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Cisco Router Security Audit Report")
    
    y = height - 80
    c.setFont("Helvetica", 10)
    
    for index, row in df.iterrows():
        if y < 80:  # Check if we need a new page
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)

        # Draw ID and Check Point
        c.setFillColor(colors.black)
        c.drawString(50, y, f"ID: {row.get('S. No / CIS Control No', 'N/A')} - {row.get('Check Point', 'Unknown')}")
        y -= 15
        
        # Color code the status
        status = str(row['Compliance Status (Pass/Fail)'])
        if status == "Pass":
            c.setFillColor(colors.green)
        elif status == "Fail":
            c.setFillColor(colors.red)
        else:
            c.setFillColor(colors.orange)
            
        c.drawString(70, y, f"Status: {status}")
        
        # Draw Remarks
        c.setFillColor(colors.black)
        c.drawString(180, y, f"Remark: {row['Audit Remarks']}")
        
        y -= 20
        c.setStrokeColor(colors.lightgrey)
        c.line(50, y+5, 550, y+5)
        y -= 10
        
    c.save()

def run_audit():
    # Get the directory where this script is located
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, CONFIG_FILE)
    checklist_path = os.path.join(base_path, CHECKLIST_FILE)

    print(f"--- Starting Audit ---")
    print(f"Reading Config: {config_path}")
    print(f"Reading Checklist: {checklist_path}")

    # 1. Load Files
    if not os.path.exists(config_path) or not os.path.exists(checklist_path):
        print("ERROR: Could not find config or checklist file in the folder!")
        return

    with open(config_path, 'r') as f:
        config_text = f.read()
    
    # Read the Excel file
    try:
        df = pd.read_excel(checklist_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # 2. Analysis Logic
    vty_blocks = re.findall(r'line vty.*?!', config_text, re.DOTALL)
    results = []

    for _, row in df.iterrows():
        # Get column names (handles cases where Excel columns have leading/trailing spaces)
        row_dict = row.to_dict()
        cp = str(row_dict.get('Check Point', '')).lower()
        
        status = "Fail"
        remark = "Requirement not found"

        # Check Logic
        if "ios version" in cp:
            match = re.search(r'^version (\d+\.\d+)', config_text, re.MULTILINE)
            if match: status, remark = "Pass", f"Version {match.group(1)} active"
            
        elif "hostname" in cp:
            match = re.search(r'^hostname (\S+)', config_text, re.MULTILINE)
            if match: status, remark = "Pass", f"Hostname {match.group(1)} configured"
            
        elif "password encryption" in cp:
            if "service password-encryption" in config_text:
                status, remark = "Pass", "Encryption service enabled"
                
        elif "telnet" in cp:
            telnet_found = any("telnet" in b.lower() and "transport input" in b.lower() for b in vty_blocks)
            if not telnet_found:
                status, remark = "Pass", "Telnet disabled on VTY"
            else:
                remark = "Telnet detected in transport input"
                
        elif "ssh" in cp:
            if "ip ssh version 2" in config_text:
                status, remark = "Pass", "SSHv2 is active"
            else:
                remark = "SSHv2 command missing"
                
        elif "aaa" in cp:
            if "aaa new-model" in config_text:
                status, remark = "Pass", "AAA new-model enabled"
                
        elif "banner" in cp:
            if re.search(r'^banner (motd|login)', config_text, re.MULTILINE):
                status, remark = "Pass", "Banner configured"
                
        elif "timeout" in cp:
            # Matches exec-timeout if it's NOT followed by '0 0'
            if re.search(r'exec-timeout ([1-9]\d* \d+|\d+ [1-9]\d*)', config_text):
                status, remark = "Pass", "Configured"
            else:
                remark = "Timeout set to infinite (0 0) or missing"
        else:
            status, remark = "Manual", "Check manually"

        row_dict['Compliance Status (Pass/Fail)'] = status
        row_dict['Audit Remarks'] = remark
        results.append(row_dict)

    # 3. Save Reports
    final_df = pd.DataFrame(results)
    
    # Save CSV
    final_df.to_csv(os.path.join(base_path, 'Audit_Report.csv'), index=False)
    # Save TXT
    with open(os.path.join(base_path, 'Audit_Report.txt'), 'w') as f:
        f.write(final_df.to_string(index=False))
    # Save PDF
    generate_pdf(final_df, os.path.join(base_path, 'Audit_Report.pdf'))

    print("--- SUCCESS ---")
    print("Files generated: Audit_Report.csv, Audit_Report.txt, Audit_Report.pdf")

if __name__ == "__main__":
    run_audit()