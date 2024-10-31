# Fresh Harvest Veggies - README

This project is a user interface created using Flask, focusing on building an e-commerce platform for fresh produce delivery. 
## Setup Instructions

### 1. **Create the Database**
   Create a database named `fresh_harvest`.

   ```sql
   CREATE DATABASE IF NOT EXISTS fresh_harvest;
   USE fresh_harvest;
   
   CREATE TABLE IF NOT EXISTS customers (
       id INT AUTO_INCREMENT PRIMARY KEY,
       name VARCHAR(255) NOT NULL,
       email VARCHAR(255) NOT NULL UNIQUE,
       password VARCHAR(255) NOT NULL,
       address VARCHAR(255),
       account_balance FLOAT,
       created_at DATETIME
   );
   
   -- Include similar CREATE TABLE commands for other tables
   ```

### 2. **Insert Initial Data**
   Run `insert_data.py`. This script creates the necessary tables and inserts initial data into the database, including customers, staff members, vegetables, and premade boxes.

### 3. **Testing**
   `test_models.py` is a script designed to test the model objects and their functionality. It will help you verify if the database was created successfully. Run the test using the following terminal command:

   ```sh
   pytest tests/test_models.py
   pytest tests/test_app.py

   ```
### 4. **Run the Application**
   After verifying the database setup, run `app.py` to start the application:

   ```sh
   flask run
   ```

   You can then access the application at `http://127.0.0.1:5000/`.

## User Information

There are two types of user accounts:

- **Customers**:
  - **Email**: `alice@example.com`
  - **Password**: `alice123`

- **Staff**:
  - **Email**: `parkerstaff@example.com`
  - **Password**: `parker123`

## Customer Features

Customers can:
1. Log in and log out.
2. View available vegetables and premade boxes.
3. Order vegetables and premade boxes. Premade boxes are assembled based on size. During checkout, customers can pay using a credit or debit card, or have the amount deducted from their account balance.
4. View details of current orders.
5. Cancel their current order if it hasn’t been fulfilled yet.
6. View details of previous orders.
7. View their account details and top up their account balance.

## Staff Features

Staff members can:
1. Log in and log out.
2. View all available vegetables and premade boxes.
3. View all current orders and their details.
4. View all previous orders and their details.
5. View details of all customers.
6. Generate a list of all customers.
7. Generate total sales for the week, month, and year.
8. View the most popular items.

## Notes

- The payment method for placing orders is simulated. Only account balance deduction is validated. Other payment methods (credit/debit card) do not have strict input validation in this version.

- The application is hosted on PythonAnywhere and can be accessed here: https://yuxuanpeng642.pythonanywhere.com/

- GitHub:https://github.com/Yuxuan-Peng-1156507/COMP642_S2.git

If you have any questions or issues, feel free to reach out!
