# E-Commerce Application Installation Guide

This guide will help you set up the complete e-commerce application with both the FastAPI backend and Laravel frontend.

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.8+** with pip
- **PHP 8.2+** 
- **Composer** (PHP package manager)
- **Node.js 16+** with npm
- **MySQL 8.0+** or **MariaDB 10.4+**
- **Git** (for version control)

## Project Structure

```
Ecom/
├── app/                    # FastAPI Backend
│   ├── main.py
│   ├── routers/
│   ├── models/
│   └── db.py
├── e-com/                  # Laravel Frontend
│   ├── app/
│   ├── resources/
│   ├── routes/
│   └── public/
├── database.sql            # Database schema and sample data
├── requirements.txt        # Python dependencies
└── INSTALLATION.md        # This file
```

## Step 1: Database Setup

### 1.1 Create Database

```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE ecommerce_db;

# Create user (optional but recommended)
CREATE USER 'ecom_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON ecommerce_db.* TO 'ecom_user'@'localhost';
FLUSH PRIVILEGES;

# Exit MySQL
EXIT;
```

### 1.2 Import Sample Data

```bash
# Navigate to project root
cd /path/to/Ecom

# Import database schema and sample data
mysql -u root -p ecommerce_db < database.sql
```

### 1.3 Verify Database

```bash
# Check if tables were created
mysql -u root -p ecommerce_db -e "SHOW TABLES;"

# Should show: categories, customers, order_items, orders, product_images, products, variations
```

## Step 2: FastAPI Backend Setup

### 2.1 Setup Python Environment

```bash
# Navigate to the app directory
cd app

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r ../requirements.txt
```

### 2.2 Configure Database Connection

Edit `app/db.py` and update the database connection settings:

```python
# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # or 'ecom_user' if you created a separate user
    'password': 'your_mysql_password',
    'database': 'ecommerce_db',
    'charset': 'utf8mb4'
}
```

### 2.3 Start FastAPI Server

```bash
# Make sure you're in the app directory with virtual environment activated
cd app
source venv/bin/activate  # if not already activated

# Start the FastAPI server
uvicorn main:app --reload

# Server will start at http://127.0.0.1:8000
```

### 2.4 Test API Endpoints

```bash
# Test in a new terminal window
curl http://127.0.0.1:8000/customers
curl http://127.0.0.1:8000/products
curl http://127.0.0.1:8000/categories

# You should get JSON responses with data
```

## Step 3: Laravel Frontend Setup

### 3.1 Install PHP Dependencies

```bash
# Navigate to Laravel directory
cd e-com

# Install Composer dependencies
composer install
```

### 3.2 Environment Configuration

```bash
# Copy environment file
cp .env.example .env

# Generate application key
php artisan key:generate
```

### 3.3 Configure Environment

Edit the `.env` file with the following settings:

```env
# Basic Laravel Configuration
APP_NAME=EcomStore
APP_ENV=local
APP_DEBUG=true
APP_URL=http://localhost:8080

# Session Configuration
SESSION_DRIVER=file
SESSION_LIFETIME=120

# E-commerce API Configuration
ECOMMERCE_API_URL=http://localhost:8000
ECOMMERCE_API_TIMEOUT=30

# E-commerce Features
FEATURE_GUEST_CHECKOUT=true
FEATURE_PRODUCT_COMPARISON=true
FEATURE_COUPONS=true

# E-commerce Settings
ECOMMERCE_SITE_NAME="EcomStore"
ECOMMERCE_SITE_DESCRIPTION="Your trusted online shopping destination"
ECOMMERCE_CURRENCY=USD
ECOMMERCE_CURRENCY_SYMBOL="$"

# Cache Settings (optional)
ECOMMERCE_CACHE_ENABLED=false

# Email Settings (optional)
ECOMMERCE_EMAIL_ENABLED=false
ECOMMERCE_EMAIL_FROM=noreply@ecomstore.com
ECOMMERCE_EMAIL_FROM_NAME="EcomStore"
```

### 3.4 Install Frontend Dependencies (Optional)

```bash
# Install Node.js dependencies (if you plan to customize assets)
npm install

# Build assets
npm run build
```

### 3.5 Clear Caches

```bash
# Clear all caches
php artisan cache:clear
php artisan config:clear
php artisan route:clear
php artisan view:clear
```

### 3.6 Start Laravel Server

```bash
# Start Laravel development server
php artisan serve --port=8080

# Server will start at http://127.0.0.1:8080
```

## Step 4: Verification

### 4.1 Check Both Servers

1. **FastAPI Backend**: http://127.0.0.1:8000
   - Should show FastAPI documentation
   - API endpoints should return JSON data

2. **Laravel Frontend**: http://127.0.0.1:8080
   - Should show the e-commerce homepage
   - Products and categories should load from API

### 4.2 Test Key Functionality

1. **Browse Products**: Navigate to products page
2. **Add to Cart**: Try adding products to cart
3. **Customer Registration**: Create a new customer account
4. **Place Order**: Complete a test order (guest checkout)
5. **Admin Panel**: Access admin panel at http://127.0.0.1:8080/admin

## Step 5: Production Considerations

### 5.1 Environment Variables

For production deployment, update these settings:

```env
# Production settings
APP_ENV=production
APP_DEBUG=false
ECOMMERCE_API_URL=https://your-api-domain.com
ECOMMERCE_CACHE_ENABLED=true
ECOMMERCE_EMAIL_ENABLED=true
```

### 5.2 Security

- Change default passwords
- Use environment variables for sensitive data
- Enable HTTPS for both frontend and backend
- Implement proper authentication/authorization
- Set up firewall rules

### 5.3 Performance

- Enable caching (Redis/Memcached)
- Optimize database queries
- Use CDN for static assets
- Configure proper web server (Nginx/Apache)

## Troubleshooting

### Common Issues

1. **"Connection refused" errors**
   - Ensure FastAPI backend is running on port 8000
   - Check firewall settings
   - Verify API URL in Laravel .env file

2. **"No application encryption key" error**
   - Run: `php artisan key:generate`
   - Ensure .env file exists and is readable

3. **Database connection errors**
   - Verify MySQL is running
   - Check database credentials in `app/db.py`
   - Ensure database and tables exist

4. **Cart not working**
   - Check session permissions: `chmod -R 775 storage/`
   - Verify session driver in .env

5. **Images not displaying**
   - Check if placeholder URLs are accessible
   - Verify image upload directory permissions

### Debug Mode

Enable debug mode for detailed error messages:

```env
# In Laravel .env file
APP_DEBUG=true

# Check Laravel logs
tail -f storage/logs/laravel.log

# Check FastAPI logs in terminal where uvicorn is running
```

### Port Conflicts

If ports 8000 or 8080 are in use:

```bash
# For FastAPI (change port)
uvicorn main:app --reload --port 8001

# Update Laravel .env
ECOMMERCE_API_URL=http://localhost:8001

# For Laravel (change port)
php artisan serve --port=8081
```

## API Documentation

Once FastAPI is running, access the interactive API documentation:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## Default Test Data

The database comes with sample data:

### Customers
- john@example.com / password
- jane@example.com / password

### Categories
- Clothing
- Electronics  
- Shoes

### Products
- T-Shirt ($15.99)
- Jeans ($45.50)
- Smartphone ($299.99)
- Running Shoes ($60.00)

## Support

For issues and questions:

1. Check this installation guide
2. Review error logs
3. Verify all prerequisites are installed
4. Ensure both servers are running
5. Test API endpoints directly

## Next Steps

After successful installation:

1. Customize the design and branding
2. Add more products and categories
3. Configure payment gateways
4. Set up email notifications
5. Implement advanced features (reviews, wishlist, etc.)
6. Deploy to production server

---

**Note**: This installation assumes a development environment. For production deployment, additional security measures, performance optimizations, and proper server configuration are required.