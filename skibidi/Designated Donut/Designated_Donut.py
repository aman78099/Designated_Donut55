# Import the Flask tools used to create the website
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os

# Create the Flask application
designated_donut = Flask(__name__)

# New secret key every time the Flask server starts
designated_donut.secret_key = os.urandom(24)

# Make user sessions temporary so they end when the browser session ends
designated_donut.config["SESSION_PERMANENT"] = False

# Set the file path to the SQLite database
DATABASE = "/Users/aman/skibidi/Designated Donut/Designated_Donut.db"

# Creates the login page and allows users to submit their email and password
@designated_donut.route("/login", methods=["GET", "POST"])
def login_page():

    # Checks whether the user submitted the login form
    if request.method == "POST":

        # Get the email and password entered by the user from the form
        email = request.form.get("email")
        password = request.form.get("password")

        # Connects to the SQLite database
        conn = sqlite3.connect(DATABASE)

        # Creates a cursor so SQL commands can be executed
        c = conn.cursor()

        # Searches the Users table for an account with the entered email
        user = c.execute("""
            SELECT * FROM Users
            WHERE email = ?
        """, (email,)).fetchone()

        # Email does not exist
        if not user:
            conn.close()
            return render_template(
                "login.html",
                error="Account not found. Please create one."
            )

        # Email exists, so check the password
        if user[3].startswith("scrypt:"):
            password_correct = check_password_hash(user[3], password)
        else:
            password_correct = (user[3] == password)

        # Password is wrong
        if not password_correct:
            conn.close()

            return render_template(
                "login.html",
                error="Wrong password. Please try again."
            )

        # Get the temporary guest cart BEFORE clearing the session
        guest_cart = session.get("guest_cart", {})

        # Clear the old session
        session.clear()

        # Log in the user
        session["user_id"] = user[0]

        # Move guest cart into this user's database cart
        for product_id, quantity in guest_cart.items():

            # Checks whether the product is already in the logged-in user's cart
            existing = c.execute("""
                SELECT quantity
                FROM Cart_Items
                WHERE user_id = ? AND product_id = ?
            """, (user[0], product_id)).fetchone()

            if existing:

                # Updates the existing cart item by adding the guest cart quantity
                c.execute("""
                    UPDATE Cart_Items
                    SET quantity = quantity + ?
                    WHERE user_id = ? AND product_id = ?
                """, (quantity, user[0], product_id))

            else:

                # Adds the guest cart product to the user's database cart
                c.execute("""
                    INSERT INTO Cart_Items
                    (user_id, product_id, quantity)
                    VALUES (?, ?, ?)
                """, (user[0], product_id, quantity))

        conn.commit()

        print("Logged in as user:", session["user_id"])

        # Saves all changes made to the database
        conn.close()

        # Sends the user to the home page after successfully logging in
        return redirect(url_for("home_page"))

    # Displays the login page when the user has not submitted the login form
    return render_template("login.html")


# Creates the signup route and allows users to create a new account
@designated_donut.route('/signup', methods=['POST'])
def signup():

    # Connects to the SQLite database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Gets the user's name from the signup form
    name = request.form.get('name')

    # Gets the user's email from the signup form
    email = request.form.get('email')

    # Gets the user's password from the signup form
    password = request.form.get('password')

    # Gets the password confirmation from the signup form
    confirm_password = request.form.get('confirm_password')

    # Checks whether the two passwords entered by the user match
    if password != confirm_password:
        conn.close()
        # Returns the user to the login page with an error message
        return render_template(
            "login.html",
            error="Passwords do not match."
        )

    # Searches the Users table to check whether an account with this email already exists
    existing_user = c.execute("""
        SELECT * FROM Users
        WHERE email = ?
    """, (email,)).fetchone()

    # Checks whether an account with the entered email already exists
    if existing_user:
        conn.close()
        return render_template(
            "login.html",
            error="Account already exists. Please sign in."
        )

    # Finds the highest user ID currently stored in the Users table
    last_user = c.execute("""
        SELECT MAX(user_id) FROM Users
    """).fetchone()

    # If there are no existing users, starts the user ID at 1
    if last_user[0] is None:
        new_user_id = 1
    
    # Otherwise, creates the new user ID by adding 1 to the previous highest ID
    else:
        new_user_id = last_user[0] + 1

    # Hashes the user's password before storing it in the database
    hashed_password = generate_password_hash(password)

    # Adds the new user's details to the Users table
    c.execute("""
        INSERT INTO Users
        (user_id, name, email, password_hash)
        VALUES (?, ?, ?, ?)
    """, (new_user_id, name, email, hashed_password))

    # Saves the new account to the database
    conn.commit()
    conn.close()

    # Sends the newly registered user to the login page
    return redirect(url_for('login_page'))


# Creates the logout route for users who want to sign out
@designated_donut.route("/logout")
def logout():

    # Clears all information stored in the user's session
    session.clear()

    # Sends the user to the login page after logging out
    return redirect(url_for("login_page"))


# Create the route for the cart page and define the function that displays the cart
@designated_donut.route("/cart")
def cart_page():

    # Connect to the SQLite database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Check if the user is logged in and retrieve their cart from the database
    if "user_id" in session:

        # Get the logged-in user's ID from the session
        user_id = session["user_id"]

        # Retrieve the products in the logged-in user's cart, including product details,
        # quantity, and the total price for each product
        cart_items = c.execute("""
            SELECT
                Products.product_id,
                Products.product_name,
                Products.price * Cart_Items.quantity AS total_price,
                Cart_Items.quantity
            FROM Cart_Items
            JOIN Products
            ON Cart_Items.product_id = Products.product_id
            WHERE Cart_Items.user_id = ?
        """, (user_id,)).fetchall()

    # Retrieve the cart from the session if the user is not logged in
    else:

        # Get the guest user's cart from the session, or create an empty cart if none exists
        guest_cart = session.get("guest_cart", {})

        # Create an empty list to store the guest user's cart items
        cart_items = []

        # Loop through each product and its quantity in the guest user's cart
        for product_id, quantity in guest_cart.items():

            # Retrieve the product ID, product name, and price from the database
            product = c.execute("""
                SELECT
                    product_id,
                    product_name,
                    price
                FROM Products
                WHERE product_id = ?
            """, (product_id,)).fetchone()

            # Add the product information and calculated total price to the cart
            if product:
                cart_items.append((
                    product[0],
                    product[1],
                    product[2] * quantity,
                    quantity
                ))

    # Calculate the total cost of all items in the cart
    total_cost = sum(item[2] for item in cart_items)

    # Close the database connection
    conn.close()

    # Display the cart page and pass the cart items and total cost to the HTML template
    return render_template(
        "cart.html",
        cart_items=cart_items,
        total_cost=total_cost
    )


# Create the route for adding a product to the cart using a POST request
@designated_donut.route("/add_to_cart", methods=["POST"])
def add_to_cart():

    # Get the product ID submitted from the form
    product_id = request.form.get("product_id")

    # Make sure a product ID was actually provided
    if product_id is None:
        return redirect(url_for("home_page"))

    # Add the product to the guest user's cart stored in the session
    if "user_id" not in session:

        guest_cart = session.get("guest_cart", {})

        # Increase the quantity if the product is already in the cart
        # Otherwise, add the product with a quantity of 1
        if product_id in guest_cart:
            guest_cart[product_id] += 1
        else:
            guest_cart[product_id] = 1

        # Save the updated guest cart to the session
        session["guest_cart"] = guest_cart

        return redirect(url_for("cart_page"))

    # Add the product to the logged-in user's cart in the database
    user_id = session["user_id"]

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Check whether the selected product is already in the user's cart
    existing = c.execute("""
        SELECT quantity
        FROM Cart_Items
        WHERE user_id = ? AND product_id = ?
    """, (user_id, product_id)).fetchone()

    # Increase the quantity if the product is already in the cart
    if existing:
        c.execute("""
            UPDATE Cart_Items
            SET quantity = quantity + 1
            WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id))
    else:

        # Add the product to the database with a quantity of 1 if it is not already in the cart
        c.execute("""
            INSERT INTO Cart_Items
            (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (user_id, product_id, 1))

    # Save the changes and close the database connection
    conn.commit()
    conn.close()

    return redirect(url_for("cart_page"))


# Create the route for increasing the quantity of a product in the cart
@designated_donut.route("/increase_cart", methods=["POST"])
def increase_cart():

    # Get the product ID submitted from the form
    product_id = request.form.get("product_id")

    # Increase the quantity in the guest user's cart stored in the session
    if "user_id" not in session:

        guest_cart = session.get("guest_cart", {})

        guest_cart[product_id] = guest_cart.get(product_id, 0) + 1

        session["guest_cart"] = guest_cart

        return redirect(url_for("cart_page"))

    # Increase the quantity in the logged-in user's cart stored in the database
    user_id = session["user_id"]

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Update the product quantity by increasing it by 1
    c.execute("""
        UPDATE Cart_Items
        SET quantity = quantity + 1
        WHERE user_id = ? AND product_id = ?
    """, (user_id, product_id))

    # Save the changes and close the database connection
    conn.commit()
    conn.close()

    # Redirect the user back to the cart page
    return redirect(url_for("cart_page"))


# Create the route for increasing the quantity of a product in the cart using a POST request
@designated_donut.route("/decrease_cart", methods=["POST"])
def decrease_cart():

    product_id = request.form.get("product_id")

    # Increase the product quantity for a guest user's cart stored in the session
    if "user_id" not in session:

        guest_cart = session.get("guest_cart", {})

        if product_id in guest_cart:

            guest_cart[product_id] -= 1

            if guest_cart[product_id] <= 0:
                del guest_cart[product_id]

        session["guest_cart"] = guest_cart

        return redirect(url_for("cart_page"))

    # Increase the product quantity for a logged-in user's cart stored in the database
    user_id = session["user_id"]

# Connect to the SQLite database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

# Check the current quantity of the selected product in the user's cart
    existing = c.execute("""
        SELECT quantity
        FROM Cart_Items
        WHERE user_id = ? AND product_id = ?
    """, (user_id, product_id)).fetchone()

    # Decrease the quantity if more than one item is in the cart
    if existing:
        if existing[0] > 1:
            c.execute("""
                UPDATE Cart_Items
                SET quantity = quantity - 1
                WHERE user_id = ? AND product_id = ?
            """, (user_id, product_id))

        # Remove the product from the cart if its quantity is already 1
        else:
            c.execute("""
                DELETE FROM Cart_Items
                WHERE user_id = ? AND product_id = ?
            """, (user_id, product_id))

    # Save the updated quantity and close the database connection
    conn.commit()
    conn.close()

    return redirect(url_for("cart_page"))


# Create the route for removing a product from the cart using a POST request
@designated_donut.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():

    product_id = request.form.get("product_id")

    # Remove the product from the guest user's cart stored in the session
    if "user_id" not in session:

        guest_cart = session.get("guest_cart", {})

        # Check if the product exists in the guest cart before removing it
        if product_id in guest_cart:
            del guest_cart[product_id]

        # Save the updated guest cart to the session
        session["guest_cart"] = guest_cart

        return redirect(url_for("cart_page"))

    # Remove the product from the logged-in user's cart stored in the database
    user_id = session["user_id"]

    # Connect to the SQLite database

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Remove the selected product from the user's cart
    c.execute("""
        DELETE FROM Cart_Items
        WHERE user_id = ? AND product_id = ?
    """, (user_id, product_id))

    # Save the changes and close the database connection
    conn.commit()
    conn.close()

    return redirect(url_for("cart_page"))


# Create the checkout route and allow the checkout process to be submitted using a POST request
@designated_donut.route("/checkout", methods=["POST"])
def checkout():

    # Make sure the user is logged in before allowing them to checkout
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    # Get the logged-in user's ID from the session
    user_id = session["user_id"]

    # Connect to the database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Retrieve all products and quantities currently in the user's cart
    cart_items = c.execute("""
        SELECT product_id, quantity
        FROM Cart_Items
        WHERE user_id = ?
    """, (user_id,)).fetchall()

    # If the cart is empty, close the database and return to the cart page
    if not cart_items:
        conn.close()
        return redirect(url_for("cart_page"))

    # Find the most recent order ID so a new unique order ID can be created
    last_order = c.execute("""
        SELECT MAX(order_id)
        FROM Orders
    """).fetchone()

    # Start the order ID at 1 if there are no previous orders
    if last_order[0] is None:
        new_order_id = 1
    else:
        new_order_id = last_order[0] + 1

    # Get the current date and format it as day/month/year
    order_date = datetime.now().strftime("%d/%m/%Y")

    # Create a new order record for the logged-in user
    c.execute("""
        INSERT INTO Orders
        (order_id, user_id, order_date)
        VALUES (?, ?, ?)
    """, (new_order_id, user_id, order_date))

    # Add each product from the cart to the new order
    for product_id, quantity in cart_items:

        # Remove all items from the user's cart after the order has been created
        c.execute("""
            INSERT INTO Order_Items
            (order_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (new_order_id, product_id, quantity))

    c.execute("""
        DELETE FROM Cart_Items
        WHERE user_id = ?
    """, (user_id,))


    # Save the order, order items, and cart changes to the database
    conn.commit()
    conn.close()

    # Save the order, order items, and cart changes to the database
    return redirect(url_for("thankyou_page"))


# Create the route for the thank-you page
@designated_donut.route("/thankyou")
def thankyou_page():

    # Make sure the customer is logged in before displaying their orders
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    # Get the logged-in customer's user ID from the session
    user_id = session["user_id"]

    # Connect to the database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Retrieve the customer's orders, including the order date, products, prices, and quantities
    # The newest orders are displayed first
    orders = c.execute("""
        SELECT
            Orders.order_id,
            Orders.order_date,
            Products.product_name,
            Products.price,
            Order_Items.quantity
        FROM Orders
        JOIN Order_Items
        ON Orders.order_id = Order_Items.order_id
        JOIN Products
        ON Order_Items.product_id = Products.product_id
        WHERE Orders.user_id = ?
        ORDER BY Orders.order_id DESC
    """, (user_id,)).fetchall()

    # Close the database connection
    conn.close()

    # Display the thank-you page and pass the customer's order information to the templatex
    return render_template(
        "thankyou.html",
        orders=orders
    )


# Create the route for the website home page
@designated_donut.route('/')
def home_page():
        # Display the home page template
    return render_template('index.html')


# Create the route for the About page
@designated_donut.route('/about')
def about_page():
        # Display the About page template
    return render_template('about.html')


# Create the route for the Order page
@designated_donut.route('/order')
def order_page():

    # Connect to the SQLite database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Retrieve all products from the Products table
    products = c.execute("""
        SELECT * FROM Products
    """).fetchall()

    # Close the database connection
    conn.close()

    # Display the Order page and pass the product information to the template
    return render_template("order.html", products=products)


# Create the route for the Review page
@designated_donut.route("/review")
def review_page():

    # Connect to the SQLite database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Retrieve all reviews along with the customer's name, rating, and review date
    # Display the most recent reviews first
    reviews = c.execute("""
        SELECT
            Users.name,
            Reviews.review_text,
            Reviews.rating,
            Reviews.review_date
        FROM Reviews
        JOIN Users
        ON Reviews.user_id = Users.user_id
        ORDER BY Reviews.review_date DESC
    """).fetchall()

    # Close the database connection
    conn.close()

    # Display the Review page and pass the reviews to the template
    return render_template(
        "review.html",
        reviews=reviews
    )


# Create the route for submitting a new review using a POST request
@designated_donut.route("/add_review", methods=["POST"])
def add_review():

    # Make sure the customer is logged in before allowing them to submit a review
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    
    # Get the logged-in customer's user ID from the session
    user_id = session["user_id"]

    # Get the review details submitted from the form
    review_text = request.form.get("review_text")
    rating = request.form.get("rating")
    review_date = request.form.get("review_date")

    # Connect to the SQLite database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Find the highest existing review ID to create a new unique review ID
    last_review = c.execute("""
        SELECT MAX(review_id)
        FROM Reviews
    """).fetchone()

    # Start the review ID at 10001 if there are no previous reviews
    if last_review[0] is None:
        new_review_id = 10001
    else:
        new_review_id = last_review[0] + 1

    # Add the new review and its details to the Reviews table
    c.execute("""
        INSERT INTO Reviews
        (review_id, user_id, review_text, rating, review_date)
        VALUES (?, ?, ?, ?, ?)
    """, (
        new_review_id,
        user_id,
        review_text,
        rating,
        review_date
    ))

    # Save the new review and close the database connection
    conn.commit()
    conn.close()

    # Redirect the customer back to the Review page after submitting the review
    return redirect(url_for("review_page"))


# Create the route for the Feedback page
@designated_donut.route('/feedback')
def feedback_page():    
    # Display the Feedback page template
    return render_template('feedback.html')


# Create an error handler for server errors with a 500 status code
@designated_donut.errorhandler(500)
def handle_500(error):

    # Display the error page with information about the server error
    return render_template(
        'Error.html',
        error_code=500,
        error_title='Server Error',
        error_message='Oops! Something went wrong on our end.',
        error_details='Our team has been notified. Please try again later.',
        current_user=session.get('user_id')
    ), 500


# Create an error handler for access forbidden errors with a 403 status code
@designated_donut.errorhandler(403)
def handle_403(error):

    # Display the error page with information about the access error
    return render_template(
        'Error.html',
        error_code=403,
        error_title='Access Forbidden',
        error_message="You don't have permission to access this resource.",
        error_details='If you believe this is a mistake, please contact support.',
        current_user=session.get('user_id')
    ), 403


# Create an error handler for bad requests with a 400 status code
@designated_donut.errorhandler(400)
def handle_400(error):

    # Display the error page with information about the bad request
    return render_template(
        'Error.html',
        error_code=400,
        error_title='Bad Request',
        error_message='The request could not be understood by the server.',
        error_details='Please check your input and try again.',
        current_user=session.get('user_id')
    ), 400


# Create an error handler for pages that cannot be found with a 404 status code
@designated_donut.errorhandler(404)
def handle_404(error):

        # Display the error page with information about the missing page
    return render_template(
        "Error.html",
        error_code=404,
        error_title="Page Not Found",
        error_message="The page you are looking for could not be found.",
        error_details="Please check the URL and try again.",
        current_user=session.get("user_id")
    ), 404


# Start the Flask application in debug mode using port 8000
if __name__ == '__main__':
    designated_donut.run(debug=True, port=8000)