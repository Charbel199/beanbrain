# BeanBrain

[Beancount](https://github.com/beancount/beancount) is great, but I kept running into these issues:
- I couldn't add transactions while driving (safely without typing).
- I couldn't access my finances and add entries from anywhere.
- I kept forgetting to log my spotify and google recurring payments.

Thus, I present **BeanBrain**, a self-hosted automation layer for Beancount that adds recurring transactions, LLM-powered entry creation, and backups, so you can manage your finances better (with Fava) from anywhere.

## Features

- **Recurring Transactions**: Automatically create transactions on daily, weekly, monthly, or yearly schedules using flexible cron expressions.

- **LLM-Powered Entry Creation**: Just describe a transaction in plain language and a language model will infer accounts, amounts, and generate a proper Beancount entry.

- **Fava Frontend**: We love [Fava](https://beancount.github.io/fava/), an open-source web interface for browsing and analyzing your Beancount ledger.

- **Easy Deployment**: Fully Docker-ready with Compose support, self-hosting is quick and simple.

- **Optional Backups**: Easily enable automatic backups of your Beancount file to Google Drive for peace of mind.



## Quick Start

### Prerequisites

- A server with Docker and Docker Compose
- A Beancount ledger file

### 1. Setup Your Environment

```bash
# Clone the repository
git clone https://github.com/Charbel199/beanbrain.git
cd beanbrain

# Copy the example environment file
cp example.env .env

# Edit the `TO CHANGE` environment variables
nano .env
```

### 2. Configure Your Beancount File

```bash
# Add your Beancount file to the data directory
cp /path/to/your/ledger.beancount ./data/budget.beancount

# Update the filename in .env if different
LOCAL_BEANCOUNT_FILE_NAME=your-ledger.beancount
```


### 3. (Optional) Set Up Rclone for Cloud Backups

If you want to back up your Beancount files to a cloud service like Google Drive or Dropbox using `rclone`, follow these steps.

#### Step 1: Install rclone

```bash
curl https://rclone.org/install.sh | sudo bash
```

#### Step 2: Configure rclone Remotes

```bash
rclone config
```

Follow the interactive prompts to create a remote (e.g., `gdrive`) for your preferred cloud provider.

> ⚠️ **Note:** Avoid using `sudo rclone config` unless necessary. Using `sudo` can store the config in the root user’s home, making it inaccessible to your app. Always run `rclone config` as your normal user.

And go for the rclone built-in client and secret (Keep them empty), we will only be doing a backup once or twice a day


### 4. Launch the Services

```bash
# Start all services
docker compose --profile backup --env-file=./.env up -d

# Start only the main services
docker compose --env-file=./.env up -d
```


### 5. Access Your Services

- **Fava Web Interface**: http://localhost:FAVA_EXTERNAL_PORT
- **API Documentation**: http://localhost:BRAIN_EXTERNAL_PORT/docs

## API Usage

### Create a Recurring Transaction

```bash
curl -X POST "http://localhost:BRAIN_EXTERNAL_PORT/automation/automations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly Rent",
    "enabled": true,
    "payload": {
      "amount": 1200.00,
      "currency": "USD",
      "from_account": "Assets:Checking",
      "to_account": "Expenses:Housing:Rent",
      "narration": "Monthly rent payment"
    },
    "cron_expression": "0 9 1 * *",
    "timezone": "America/New_York"
  }'
```

### List All Automations

```bash
curl "http://localhost:BRAIN_EXTERNAL_PORT/automation/automations"
```

### Update an Automation

```bash
curl -X PATCH "http://localhost:BRAIN_EXTERNAL_PORT/automation/automations/1" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false
  }'
```

### Create a Transaction via LLM

Set `OPENAI_API_KEY` in your `.env` for this endpoint to work.

```bash
curl -X POST "http://localhost:BRAIN_EXTERNAL_PORT/llm/append" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bought groceries at Carrefour for 23.50 EUR using my wallet"
  }'
```

- The service will infer appropriate accounts and amounts based on your ledger, recent entries, and any inline comments on account Open directives.
- The generated transaction will be appended to your Beancount file configured at `BEANCOUNT_FILE`.

## Configuration

### Main Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOCAL_BEANCOUNT_FILE_NAME` | Your Beancount ledger filename | `budget.beancount` |
| `FAVA_EXTERNAL_PORT` | Port for Fava web interface | `5000` |
| `BRAIN_EXTERNAL_PORT` | Port for BeanBrain API | `4999` |
| `DATABASE_URL` | Database connection string | `sqlite:////data/automations.db` |
| `DEFAULT_TZ` | Default timezone | `Asia/Beirut` |
| `DEFAULT_CURRENCY` | Default currency | `USD` |
| `OPENAI_API_KEY` | Open AI API Key | `-` |


### Cron Expression Examples

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Daily at 9 AM | `0 9 * * *` | Every day at 9:00 AM |
| Weekly on Monday | `0 9 * * 1` | Every Monday at 9:00 AM |
| Monthly on 1st | `0 9 1 * *` | 1st of every month at 9:00 AM |
| Yearly on Jan 1st | `0 9 1 1 *` | January 1st at 9:00 AM |

## Project Structure

- **`brain/`**: Core automation engine
- **`fava/`**: Web interface for Beancount
- **`backup/`**: Backup script
- **`data/`**: Your beancount file, backups and db

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



