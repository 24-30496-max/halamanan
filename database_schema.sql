-- ============================================
-- H.A.L.A.M.A.N.A.N DATABASE SCHEMA
-- ============================================

-- Use the database
USE halamanan07;

-- ============================================
-- 1. USERS TABLE (Parent table - create first)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    province VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================
-- 2. RESOURCES TABLE (Offers from users)
-- ============================================
CREATE TABLE IF NOT EXISTS resources (
    resource_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category VARCHAR(50) NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    start_available_date DATE,
    end_available_date DATE,
    status ENUM('Available', 'Pending', 'Completed') DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================
-- 3. REQUESTS TABLE (Looking for items)
-- ============================================
CREATE TABLE IF NOT EXISTS requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category VARCHAR(50) NOT NULL,
    needed_item VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    status ENUM('Available', 'Pending', 'Completed') DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================
-- 4. CONNECTIONS TABLE (Connections between users)
-- ============================================
CREATE TABLE IF NOT EXISTS connections (
    connection_id INT AUTO_INCREMENT PRIMARY KEY,
    requester_id INT NOT NULL,
    helper_id INT NOT NULL,
    resource_id INT,
    request_id INT,
    status ENUM('Pending', 'Approved', 'Completed', 'Rejected') DEFAULT 'Pending',
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (requester_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (helper_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id) ON DELETE CASCADE,
    FOREIGN KEY (request_id) REFERENCES requests(request_id) ON DELETE CASCADE
);

-- ============================================
-- 5. INQUIRIES TABLE (Inquire notifications)
-- ============================================
CREATE TABLE IF NOT EXISTS inquiries (
    inquiry_id INT AUTO_INCREMENT PRIMARY KEY,
    resource_id INT NOT NULL,
    buyer_id INT NOT NULL,
    seller_id INT NOT NULL,
    status ENUM('Sent', 'Viewed', 'Accepted', 'Rejected') DEFAULT 'Sent',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_inquiry (resource_id, buyer_id)
);

-- ============================================
-- 6. PAYMENTS TABLE (Payment processing)
-- ============================================
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    resource_id INT NOT NULL,
    buyer_id INT NOT NULL,
    seller_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('Cash', 'Bank Transfer', 'Online Payment') DEFAULT 'Cash',
    status ENUM('Pending', 'Completed', 'Failed', 'Cancelled') DEFAULT 'Pending',
    transaction_ref VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================
-- CREATE INDEXES
-- ============================================
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_resource_user ON resources(user_id);
CREATE INDEX idx_request_user ON requests(user_id);
CREATE INDEX idx_connection_requester ON connections(requester_id);
CREATE INDEX idx_connection_helper ON connections(helper_id);
CREATE INDEX idx_inquiry_buyer ON inquiries(buyer_id);
CREATE INDEX idx_inquiry_seller ON inquiries(seller_id);
CREATE INDEX idx_payment_buyer ON payments(buyer_id);
CREATE INDEX idx_payment_seller ON payments(seller_id);
CREATE INDEX idx_payment_status ON payments(status);
