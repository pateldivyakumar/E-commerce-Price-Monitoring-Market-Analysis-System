CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title TEXT,
    price NUMERIC(10,2),
    rating VARCHAR(20),
    product_url TEXT,
    date_collected DATE,
    upc VARCHAR(50),
    category VARCHAR(100),
    stock_quantity INT
);