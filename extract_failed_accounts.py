import re
import sys

def extract_failed_accounts(report_file: str, output_csv: str = "retry.csv"):
    """
    Extract failed account numbers from the report and create a new CSV file.
    
    Args:
        report_file: Path to the report file
        output_csv: Path to the output CSV file
    """
    failed_accounts = []
    
    # Read the report file
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all failed account numbers using regex
    # Pattern matches: "  ❌ Account: 200248329601"
    pattern = r'❌ Account:\s+(\d+)'
    matches = re.findall(pattern, content)
    
    failed_accounts = matches
    
    print(f"Found {len(failed_accounts)} failed accounts")
    
    # Write to CSV file
    with open(output_csv, 'w', encoding='utf-8') as f:
        f.write("ACCOUNTNUMBER\n")
        for account in failed_accounts:
            f.write(f"{account}\n")
    
    print(f"Created {output_csv} with {len(failed_accounts)} accounts for retry")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        report_file = sys.argv[1]
        output_csv = sys.argv[2] if len(sys.argv) > 2 else "retry.csv"
    else:
        report_file = "eligibility_report_20260512_133924.txt"
        output_csv = "retry.csv"
    
    extract_failed_accounts(report_file, output_csv)
