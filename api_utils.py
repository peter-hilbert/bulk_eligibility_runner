import os
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Load environment variables from .env file
load_dotenv()


def send_program_eligibility_query(
    account_number: str,
    programs: List[str] = ["PRP"],
    use_cache: bool = False
) -> Dict[str, Any]:
    """
    Send a GraphQL query to check program eligibilities for a given account.
    
    Args:
        account_number: The account number to check eligibility for
        programs: List of program types to check (default: ["PRP"])
        use_cache: Whether to use cached results (default: False)
    
    Returns:
        Dict containing the response data or error information
    """
    # Get configuration from environment variables
    graphql_url = os.getenv("GRAPHQL_URL")
    bearer_token = os.getenv("BEARER_TOKEN")
    
    if not graphql_url:
        raise ValueError("GRAPHQL_URL environment variable is not set")
    if not bearer_token:
        raise ValueError("BEARER_TOKEN environment variable is not set")
    
    # GraphQL query with placeholder for account number
    query = """
    query ProgramEligibilities($programs: [ProgramTypeEnum!], $useCache: Boolean) {
      account(accountNumber: "{{accountNumber}}") {
        programEligibilities(programs: $programs, useCache: $useCache) {
          programType
          isEligible
          isSuccess
          errors
        }
      }
    }
    """
    
    # Replace the account number placeholder
    query = query.replace("{{accountNumber}}", account_number)
    
    # Prepare variables
    variables = {
        "programs": programs,
        "useCache": use_cache
    }
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    # Prepare the request payload
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        # Send the GraphQL request
        response = requests.post(graphql_url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Return the JSON response
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None
        }


# Example usage
if __name__ == "__main__":
    # Example: Check eligibility for a single account
    account_number = "200177090501"  # Replace with actual account number
    
    result = send_program_eligibility_query(
        account_number=account_number,
        programs=["PRP"],
        use_cache=False
    )
    
    print(f"Result for account {account_number}:")
    print(result)
