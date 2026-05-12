import csv
import argparse
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from api_utils import send_program_eligibility_query
from typing import List, Dict, Any, Optional


def process_single_account(account_number: str) -> Dict[str, Any]:
    """
    Process a single account's eligibility check.
    
    Args:
        account_number: The account number to check
    
    Returns:
        Dict with account_number, success status, and result/error details
    """
    try:
        # Send the GraphQL query
        result = send_program_eligibility_query(
            account_number=account_number,
            programs=["PRP"],
            use_cache=False
        )
        
        # Check if request was successful
        if "error" in result:
            return {
                "account_number": account_number,
                "success": False,
                "error": result.get("error"),
                "status_code": result.get("status_code"),
                "message": f"❌ Account {account_number}: Request failed - {result.get('error')}"
            }
        elif "errors" in result:
            return {
                "account_number": account_number,
                "success": False,
                "error": result.get("errors"),
                "status_code": "GraphQL Error",
                "message": f"❌ Account {account_number}: GraphQL error - {result.get('errors')}"
            }
        else:
            # Check if the data contains any errors in the eligibility response
            if "data" in result and "account" in result["data"]:
                eligibilities = result["data"]["account"].get("programEligibilities", [])
                for eligibility in eligibilities:
                    if eligibility.get("errors"):
                        return {
                            "account_number": account_number,
                            "success": False,
                            "error": eligibility.get("errors"),
                            "status_code": "Eligibility Error",
                            "message": f"⚠️  Account {account_number}: Eligibility check had errors"
                        }
            
            return {
                "account_number": account_number,
                "success": True,
                "message": f"✓ Account {account_number}: Success"
            }
    
    except Exception as e:
        return {
            "account_number": account_number,
            "success": False,
            "error": str(e),
            "status_code": "Exception",
            "message": f"❌ Account {account_number}: Exception - {str(e)}"
        }


def process_eligibility_checks(csv_file: str = "data.csv", limit: Optional[int] = None, workers: int = 10) -> None:
    """
    Process program eligibility checks for all accounts in the CSV file.
    
    Args:
        csv_file: Path to the CSV file containing account numbers
        limit: Optional limit on the number of accounts to process (for testing)
        workers: Number of parallel workers (threads) to use (default: 10)
    """
    print(f"Starting bulk eligibility check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Reading data from: {csv_file}")
    if limit:
        print(f"Processing limit: {limit} accounts (test mode)")
    print(f"Parallel workers: {workers}")
    print("-" * 60)
    
    # Read the CSV file
    try:
        # Use utf-8-sig to handle BOM (Byte Order Mark) if present
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Get column names from first row
            fieldnames = reader.fieldnames
            
            if not fieldnames:
                print(f"Error: CSV file appears to be empty!")
                return
            
            # Find the actual column name that matches ACCOUNTNUMBER (with or without spaces)
            account_column = None
            for col in fieldnames:
                if col and col.strip().upper() == "ACCOUNTNUMBER":
                    account_column = col
                    break
            
            # Check if ACCOUNTNUMBER column exists
            if not account_column:
                print(f"Error: 'ACCOUNTNUMBER' column not found in CSV!")
                print(f"Available columns: {', '.join([col.strip() for col in fieldnames if col])}")
                return
            
            # Read all account numbers (skip empty values)
            account_numbers = []
            for row in reader:
                account_num = row.get(account_column, "").strip()
                if account_num:  # Skip empty values
                    account_numbers.append(account_num)
                    
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found!")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Apply limit if specified
    if limit and limit > 0:
        account_numbers = account_numbers[:limit]
    
    total_accounts = len(account_numbers)
    
    print(f"Found {total_accounts} accounts to process\n")
    
    # Track results
    successful_accounts = []
    failed_accounts = []
    results_details = []
    
    # Process accounts in parallel
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_account = {
            executor.submit(process_single_account, account_number): account_number
            for account_number in account_numbers
        }
        
        # Process completed tasks with progress bar
        for future in tqdm(as_completed(future_to_account), total=total_accounts, desc="Processing accounts", unit="account"):
            try:
                result = future.result()
                
                # Add to appropriate list based on success
                if result["success"]:
                    successful_accounts.append(result["account_number"])
                else:
                    failed_accounts.append({
                        "account_number": result["account_number"],
                        "error": result.get("error"),
                        "status_code": result.get("status_code")
                    })
                
                results_details.append(result["message"])
                
            except Exception as e:
                account_number = future_to_account[future]
                failed_accounts.append({
                    "account_number": account_number,
                    "error": str(e),
                    "status_code": "Future Exception"
                })
                results_details.append(f"❌ Account {account_number}: Future exception - {str(e)}")
    
    # Generate report
    generate_report(
        total_accounts=total_accounts,
        successful_accounts=successful_accounts,
        failed_accounts=failed_accounts,
        results_details=results_details
    )
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print(f"Report saved to: eligibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    print("=" * 60)


def generate_report(
    total_accounts: int,
    successful_accounts: List[str],
    failed_accounts: List[Dict[str, Any]],
    results_details: List[str]
) -> None:
    """
    Generate a text file report with processing results.
    
    Args:
        total_accounts: Total number of accounts processed
        successful_accounts: List of successful account numbers
        failed_accounts: List of failed account details
        results_details: Detailed results for each account
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"eligibility_report_{timestamp}.txt"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("BULK ELIGIBILITY CHECK REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")
        
        # Summary Section
        f.write("-" * 70 + "\n")
        f.write("SUMMARY\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total Accounts Processed: {total_accounts}\n")
        f.write(f"Successful: {len(successful_accounts)}\n")
        f.write(f"Failed: {len(failed_accounts)}\n")
        f.write(f"Success Rate: {(len(successful_accounts) / total_accounts * 100):.2f}%\n")
        f.write("\n")
        
        # Successful Accounts
        if successful_accounts:
            f.write("-" * 70 + "\n")
            f.write(f"SUCCESSFUL ACCOUNTS ({len(successful_accounts)})\n")
            f.write("-" * 70 + "\n")
            for account in successful_accounts:
                f.write(f"  ✓ {account}\n")
            f.write("\n")
        
        # Failed Accounts
        if failed_accounts:
            f.write("-" * 70 + "\n")
            f.write(f"FAILED ACCOUNTS ({len(failed_accounts)})\n")
            f.write("-" * 70 + "\n")
            for failure in failed_accounts:
                f.write(f"  ❌ Account: {failure['account_number']}\n")
                f.write(f"     Status: {failure['status_code']}\n")
                f.write(f"     Error: {failure['error']}\n")
                f.write("\n")
        
        # Detailed Log
        f.write("-" * 70 + "\n")
        f.write("DETAILED PROCESSING LOG\n")
        f.write("-" * 70 + "\n")
        for detail in results_details:
            f.write(f"{detail}\n")
        
        f.write("\n")
        f.write("=" * 70 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 70 + "\n")
    
    # Also print summary to console
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Accounts: {total_accounts}")
    print(f"Successful: {len(successful_accounts)} ({(len(successful_accounts) / total_accounts * 100):.2f}%)")
    print(f"Failed: {len(failed_accounts)} ({(len(failed_accounts) / total_accounts * 100):.2f}%)")


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Process bulk eligibility checks for accounts from a CSV file."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of accounts to process (useful for testing)"
    )
    parser.add_argument(
        "--file",
        type=str,
        default="data.csv",
        help="Path to the CSV file (default: data.csv)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of parallel workers/threads (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Run the eligibility checks
    process_eligibility_checks(csv_file=args.file, limit=args.limit, workers=args.workers)
