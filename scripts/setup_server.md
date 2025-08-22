# Caddy Reverse Proxy Setup Guide

A comprehensive guide for setting up Caddy as a reverse proxy with basic authentication and SSL/TLS termination.

## Prerequisites

- Ubuntu/Debian server with sudo privileges
- Domain names pointing to your server

## Installation

### Step 1: Install Caddy

Install Caddy on Ubuntu/Debian systems:

```bash
# Add required packages and GPG key
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg

# Add Caddy repository
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list

# Update package list and install Caddy
sudo apt update
sudo apt install caddy
```

### Step 2: Configure Caddyfile

Edit the Caddy configuration file:

```bash
sudo nano /etc/caddy/Caddyfile
```

Add your configuration:

```caddyfile
{
    auto_https disable_redirects
}

budget.DOMAIN {
    reverse_proxy localhost:5000

    basicauth {
        admin $2a$14$uVqzE8OC...your_hashed_password_here...
    }
}

api.budget.DOMAIN {
    reverse_proxy localhost:4999

    basicauth {
        admin $2a$14$...your_hashed_password...
    }
}
```

#### Generate Password Hashes

Create secure password hashes for basic authentication:

```bash
caddy hash-password --plaintext "yourpassword"
```

Replace the placeholder hashes in your Caddyfile with the generated values.

### Step 3: Start and Manage Caddy

Apply configuration changes:

```bash
# Reload configuration (when changing Caddyfile)
sudo systemctl reload caddy

# Restart service (for major changes or troubleshooting)
sudo systemctl restart caddy

# Check service status
sudo systemctl status caddy

# Enable auto-start on boot
sudo systemctl enable caddy
```

## 🔒 Firewall Configuration

Configure UFW (Uncomplicated Firewall) for security:

```bash
# Allow SSH access (recommended for remote management)
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS traffic for Caddy
sudo ufw allow 80,443/tcp

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Enable firewall
sudo ufw enable

# Check firewall status
sudo ufw status verbose
```

## 🛠️ Troubleshooting

### Check Caddy Logs

```bash
# View recent logs
sudo journalctl -u caddy --no-pager --lines 50

# Follow logs in real-time
sudo journalctl -u caddy -f
```

### Test Configuration

```bash
# Validate Caddyfile syntax
caddy validate --config /etc/caddy/Caddyfile

# Test configuration without starting service
caddy run --config /etc/caddy/Caddyfile
```


## 📝 Configuration Notes

- **Auto HTTPS**: Caddy automatically obtains and renews SSL/TLS certificates
- **Basic Auth**: Protects your applications with username/password authentication  
- **Reverse Proxy**: Forwards requests to your local applications while handling SSL termination
- **Firewall**: Restricts access to only necessary ports for enhanced security

## 🔗 Useful Resources

- [Caddy Documentation](https://caddyserver.com/docs/)
- [Caddyfile Syntax](https://caddyserver.com/docs/caddyfile)
- [Basic Authentication](https://caddyserver.com/docs/caddyfile/directives/basicauth)
- [Reverse Proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)