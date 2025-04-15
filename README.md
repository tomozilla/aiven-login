# Aiven Console Login Automation

This script automates the login process for multiple Aiven Console accounts using Selenium WebDriver.

## Prerequisites

- Python 3.6 or higher
- Chrome browser
- ChromeDriver (compatible with your Chrome version)
- Required Python packages (install using `pip install -r requirements.txt`):
  - selenium
  - python-dotenv
  - webdriver_manager

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your account credentials. The `AIVEN_ACCOUNTS` variable should contain a JSON string with different sets of accounts:
   ```json
   {
       "default": {
           "0": {"email": "your_email@example.com", "password": "your_password"},
           "1": {"email": "another_email@example.com", "password": "another_password"}
       },
       "test_set": {
           "0": {"email": "test1@example.com", "password": "test_pass1"}
       }
   }
   ```

## Usage

Run the script with the following command-line arguments:

```bash
python login.py [--accounts N] [--load-set SET_NAME]
```

Arguments:
- `--accounts N`: Number of accounts to process (default: 1)
- `--load-set SET_NAME`: Which set of credentials to use (default: "default")

Examples:
```bash
# Process one account from the default set
python login.py

# Process 2 accounts from the default set
python login.py --accounts 2

# Process 3 accounts from the test_set
python login.py --accounts 3 --load-set test_set
```

## Error Handling

- If login fails for any account, a screenshot will be saved with the filename pattern: `error_{email_prefix}_{timestamp}.png`
- The script will continue processing remaining accounts even if one fails
- The exit code will be 0 if all accounts are processed successfully, 1 if any account fails

## Security Notes

- Never commit your `.env` file to version control
- Keep your credentials secure and do not share them
- Consider using a password manager or secure credential storage system for production use
