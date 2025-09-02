-- Customers Table
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    password VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories Table
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INT DEFAULT NULL,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id) ON DELETE SET NULL
);

-- Products Table
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);

-- Product Images Table (Multiple Images per Product)
CREATE TABLE product_images (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- Variations Table (Sizes, Colors, etc.)
CREATE TABLE variations (
    variation_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    attribute_name VARCHAR(50),   -- Example: Size, Color
    attribute_value VARCHAR(50),  -- Example: Large, Red
    additional_price DECIMAL(10,2) DEFAULT 0.00,
    stock INT DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- Orders Table
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NULL,   -- NULL if guest checkout
    guest_name VARCHAR(100),
    guest_email VARCHAR(150),
    guest_phone VARCHAR(20),
    guest_address TEXT,
    total_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending','processing','shipped','completed','cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
);

-- Order Items (Products inside an order)
CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    variation_id INT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (variation_id) REFERENCES variations(variation_id) ON DELETE SET NULL
);

-- Insert Customers
INSERT INTO customers (name, email, password, phone, address) VALUES
('John Doe', 'john@example.com', 'password', '1234567890', '123 Main St, New York, USA'),
('Jane Smith', 'jane@example.com', 'password', '0987654321', '456 Park Ave, Los Angeles, USA');

-- Insert Categories
INSERT INTO categories (name, description, parent_id) VALUES
('Clothing', 'All kinds of clothes', NULL),
('Electronics', 'Electronic items and gadgets', NULL),
('Shoes', 'Different types of shoes', 1); -- child of Clothing

-- Insert Products
INSERT INTO products (category_id, name, description, price, stock) VALUES
(1, 'T-Shirt', 'Cotton T-shirt with different colors', 15.99, 100),
(1, 'Jeans', 'Blue denim jeans', 45.50, 50),
(2, 'Smartphone', 'Latest Android smartphone', 299.99, 30),
(3, 'Running Shoes', 'Lightweight running shoes', 60.00, 40);

-- Insert Product Images
INSERT INTO product_images (product_id, image_url, is_primary) VALUES
(1, 'images/tshirt1.jpg', TRUE),
(1, 'images/tshirt2.jpg', FALSE),
(2, 'images/jeans1.jpg', TRUE),
(3, 'images/phone1.jpg', TRUE),
(3, 'images/phone2.jpg', FALSE),
(4, 'images/shoes1.jpg', TRUE);

-- Insert Variations (Size & Color)
INSERT INTO variations (product_id, attribute_name, attribute_value, additional_price, stock) VALUES
(1, 'Size', 'Small', 0.00, 20),
(1, 'Size', 'Medium', 0.00, 30),
(1, 'Size', 'Large', 0.00, 50),
(1, 'Color', 'Red', 0.00, 25),
(1, 'Color', 'Blue', 0.00, 25),
(4, 'Size', '8', 0.00, 10),
(4, 'Size', '9', 0.00, 15),
(4, 'Color', 'Black', 0.00, 20);

-- Insert Orders (Guest + Registered User)
INSERT INTO orders (customer_id, guest_name, guest_email, guest_phone, guest_address, total_amount, status) VALUES
(NULL, 'Guest Buyer', 'guest@example.com', '1112223333', '789 Guest St, Chicago, USA', 75.99, 'pending'),
(1, NULL, NULL, NULL, NULL, 105.50, 'processing');

-- Insert Order Items
INSERT INTO order_items (order_id, product_id, variation_id, quantity, price) VALUES
(1, 1, 2, 2, 15.99),  -- Guest bought 2 Medium T-shirts
(1, 4, 6, 1, 60.00),  -- Guest bought 1 Shoe Size 8
(2, 2, NULL, 1, 45.50), -- Registered customer bought 1 Jeans
(2, 3, NULL, 1, 299.99); -- Registered customer bought 1 Smartphone
