# BeanBrain

Beancount was able to scratch my brain in a really nice way and with fava for the frontend, I believe that this is the main thing I need to track all my finances.

Unfortunately, a couple of features were missing and I needed to self-host it in order to reach it from anywnere.

Thus beanbrain was born, automation + self-hosting



## Features

## Features

- **Recurring Transactions**  
  Automatically create transactions on daily, weekly, monthly, or yearly schedules using flexible cron expressions.

- **REST API**  
  Clean and well-documented endpoints for easy extensibility based on what is needed.

- **Fava Frontend**  
  We love [Fava](https://beancount.github.io/fava/), an open-source web interface for browsing and analyzing your Beancount ledger.

- **Easy Deployment**  
  Fully Docker-ready with Compose support, self-hosting is quick and simple.

- **Optional Backups**  
  Easily enable automatic backups of your Beancount file to Google Drive for peace of mind.



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

### 3. Launch the Services

```bash
# Start all services
docker-compose --env-file=./.env up -d
```

### 4. (Optional) Set Up Rclone for Cloud Backups

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

And go for the rclone built-in client and secret, we will only be doing a backup once or twice a day

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
- **`data/`**: Your financial data and Beancount files

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



