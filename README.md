# Bulk Eligibility Runner

A Python tool for running bulk program eligibility checks via GraphQL API with parallel processing, progress tracking, and detailed reporting.

## Features

- 🚀 **Parallel processing** with configurable worker threads
- 📊 **Real-time progress tracking** with progress bar
- 📝 **Detailed reports** showing successes, failures, and error details
- 🔄 **Retry functionality** for failed accounts
- ⚙️ **Configurable** via command line arguments
- 🔒 **Secure** environment variable-based configuration

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Installation

1. **Clone or navigate to the project directory:**
   ```powershell
   cd path\to\bulk_eligibility_run
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

## Configuration

1. **Copy the template environment file:**
   ```powershell
   cp .env.template .env
   ```

2. **Edit `.env` and add your credentials:**
   ```env
   GRAPHQL_URL=https://your-api-endpoint.com/graphql
   BEARER_TOKEN=your_bearer_token_here
   ```

   ⚠️ **Important:** Never commit the `.env` file to version control. It's already in `.gitignore`.

## Usage

### Basic Usage

Process all accounts in `data.csv`:
```powershell
python main.py
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--file` | Path to input CSV file | `data.csv` |
| `--limit` | Limit number of accounts (for testing) | None (all accounts) |
| `--workers` | Number of parallel workers/threads | `10` |

### Examples

**Test with a small subset:**
```powershell
python main.py --limit 5
```

**Process with more parallelism:**
```powershell
python main.py --workers 20
```

**Use a different input file:**
```powershell
python main.py --file accounts.csv
```

**Combined options:**
```powershell
python main.py --file data.csv --limit 100 --workers 15
```

**See all options:**
```powershell
python main.py --help
```

## Input File Format

The input CSV file must contain an `ACCOUNTNUMBER` column:

```csv
ACCOUNTNUMBER
200199497801
200310381401
200181315601
...
```

Additional columns are ignored, so you can use CSV files with extra data.

## Output

### Console Output

The script displays:
- Configuration summary (file, limit, workers)
- Real-time progress bar
- Summary statistics (total, successful, failed, success rate)

### Report File

A timestamped report file is generated after each run:
- **Filename:** `eligibility_report_YYYYMMDD_HHMMSS.txt`
- **Contains:**
  - Summary statistics
  - List of successful accounts
  - List of failed accounts with error details
  - Detailed processing log

Example: `eligibility_report_20260512_133924.txt`

## Retrying Failed Accounts

### 1. Extract Failed Accounts

Use the utility script to create a retry CSV from a report:

```powershell
python extract_failed_accounts.py eligibility_report_20260512_133924.txt retry.csv
```

This creates a new CSV file containing only the failed accounts.

### 2. Run the Retry

Process the retry file:

```powershell
python main.py --file retry.csv
```

Or with more workers for faster processing:

```powershell
python main.py --file retry.csv --workers 20
```

## API Details

The tool sends GraphQL queries to check program eligibility:

**Query:**
```graphql
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
```

**Variables:**
- `programs`: `["PRP"]` (Payment Relief Program)
- `useCache`: `false`

## File Structure

```
bulk_eligibility_run/
├── main.py                          # Main script
├── api_utils.py                     # GraphQL API utilities
├── extract_failed_accounts.py       # Utility to extract failed accounts
├── data.csv                         # Input data file
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (don't commit!)
├── .env.template                    # Template for .env file
├── .gitignore                       # Git ignore rules
├── README.md                        # This file
├── retry.csv                        # Generated retry file (optional)
└── eligibility_report_*.txt         # Generated reports

```

## Troubleshooting

### "ACCOUNTNUMBER column not found"
- Ensure your CSV has an `ACCOUNTNUMBER` column header
- Check for extra spaces or BOM characters in the CSV file
- The script handles UTF-8 with BOM automatically

### Connection Errors (503, 500)
- These are typically temporary API issues
- Extract failed accounts and retry later
- Consider reducing `--workers` to avoid overwhelming the API

### Unicode Errors
- Reports are saved with UTF-8 encoding
- Use a UTF-8 compatible text editor to view reports

### Slow Processing
- Increase parallelism with `--workers 20` or higher
- Be careful not to overwhelm the API (rate limiting may occur)

## Performance Tips

1. **Start small:** Test with `--limit 10` before processing thousands of accounts
2. **Tune workers:** Adjust based on API rate limits and your network
3. **Monitor errors:** If many accounts fail, check API status before continuing
4. **Retry strategically:** Wait for API recovery before retrying failed accounts

## Dependencies

- `requests` - HTTP library for API calls
- `python-dotenv` - Environment variable management
- `tqdm` - Progress bar display

## License

Internal use only.

## Support

For issues or questions, contact the development team.
