Fresh Harvest Veggies - README
================================

This project is a user interface created using Flask. I haven't applied much CSS or Bootstrap for beautifying the front-end pages, but I would do so if more time was available. Before running the project, please follow these steps:

Setup Instructions:
-------------------

1. **Create the database**:
   You need to create a database named `fresh_harvest`. Afterward, edit the database's username and password in both `database.py` and `app.py`.

2. **Insert initial data**:
   Run `insert_data.py`. This script creates the necessary tables and inserts initial data into the database.

3. **Testing**:
   `test_models.py` is a script designed to test the model objects and their functionality. It will help you verify if the database was created successfully. Run the test using the following terminal command:
   
   python -m pytest test_models.py

4. **Run the application**:
   After verifying the database setup, run `app.py` to start the application and use the features step by step.

User Information:
-----------------

There are three user accounts:
- Customers: johndoe, alicesmith
- Staff: bobjohnson
  
Each account has the password: password123.
The two customers have different credit limits, meaning that their account balances can go negative up to their specific limit.

Customer Features:
------------------

Customers can:
1. Log in and log out.
2. View available vegetables and premade boxes.
3. Order vegetables and premade boxes. Premade boxes are assembled based on size. During checkout, they can pay using a credit or debit card or have the amount deducted from their account balance (which can be negative).
4. View details of current orders.
5. Cancel their current order if it hasn’t been fulfilled yet.
6. View details of previous orders.
7. View their account details.

Staff Features:
---------------

Staff members can:
1. Log in and log out.
2. View all available vegetables and premade boxes.
3. View all current orders and their details.
4. View all previous orders and their details.
5. Update the status of an order.
6. View details of all customers.
7. Generate a list of all customers.
8. Generate total sales for the week, month, and year.
9. View the most popular items.

Notes:
------

- The payment method for placing orders is simulated, so only account balance deduction is validated. Other payment methods (credit/debit card) do not have strict input validation in this version.

If you have any questions or issues, feel free to reach out!