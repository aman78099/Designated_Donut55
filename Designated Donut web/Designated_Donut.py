from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os


designated_donut = Flask(__name__)

# New secret key every time the Flask server starts
designated_donut.secret_key = os.urandom(24)

designated_donut.config["SESSION_PERMANENT"] = False

DATABASE = "Designated_Donut.db"

@designated_donut.route("/login", methods=["GET", "POST"])
def login_page():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        user = c.execute("""
            SELECT * FROM Users
            WHERE email = ?
        """, (email,)).fetchone()

        if user:
            if user[3].startswith("scrypt:"):
                password_correct = check_password_hash(user[3], password)
            else:
                password_correct = (user[3] == password)

            if password_correct:

                # Get the temporary guest cart BEFORE clearing the session
                guest_cart = session.get("guest_cart", {})

                # Clear the old session
                session.clear()

                # Log in the user
                session["user_id"] = user[0]

                # Move guest cart into this user's database cart
                for product_id, quantity in guest_cart.items():

                    existing = c.execute("""
                        SELECT quantity
                        FROM Cart_Items
                        WHERE user_id = ? AND product_id = ?
                    """, (user[0], product_id)).fetchone()

                    if existing:

                        c.execute("""
                            UPDATE Cart_Items
                            SET quantity = quantity + ?
                            WHERE user_id = ? AND product_id = ?
                        """, (quantity, user[0], product_id))

                    else:

                        c.execute("""
                            INSERT INTO Cart_Items
                            (user_id, product_id, quantity)
                            VALUES (?, ?, ?)
                        """, (user[0], product_id, quantity))

                conn.commit()

                print("Logged in as user:", session["user_id"])

                conn.close()

                return redirect(url_for("home_page"))

        conn.close()

        return render_template(
            "login.html",
            error="Account not found. Please create one."
        )

    return render_template("login.html")



@designated_donut.route('/signup', methods=['POST'])
def signup():

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if password != confirm_password:
        conn.close()
        return render_template(
            "login.html",
            error="Passwords do not match."
        )

    existing_user = c.execute("""
        SELECT * FROM Users
        WHERE email = ?
    """, (email,)).fetchone()

    if existing_user:
        conn.close()
        return render_template(
            "login.html",
            error="Account already exists. Please sign in."
        )

    last_user = c.execute("""
        SELECT MAX(user_id) FROM Users
    """).fetchone()

    if last_user[0] is None:
        new_user_id = 1
    else:
        new_user_id = last_user[0] + 1

    hashed_password = generate_password_hash(password)

    c.execute("""
        INSERT INTO Users
        (user_id, name, email, password_hash)
        VALUES (?, ?, ?, ?)
    """, (new_user_id, name, email, hashed_password))

    conn.commit()
    conn.close()

    return redirect(url_for('login_page'))



@designated_donut.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login_page"))






@designated_donut.route("/cart")
def cart_page():

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # LOGGED-IN USER
    if "user_id" in session:

        user_id = session["user_id"]

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

    # GUEST USER
    else:

        guest_cart = session.get("guest_cart", {})

        cart_items = []

        for product_id, quantity in guest_cart.items():

            product = c.execute("""
                SELECT
                    product_id,
                    product_name,
                    price
                FROM Products
                WHERE product_id = ?
            """, (product_id,)).fetchone()

            if product:

                cart_items.append((
                    product[0],
                    product[1],
                    product[2] * quantity,
                    quantity
                ))

    # Calculate total
    total_cost = sum(item[2] for item in cart_items)

    conn.close()

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total_cost=total_cost
    )




@designated_donut.route("/add_to_cart", methods=["POST"])
def add_to_cart():

    product_id = request.form.get("product_id")

    # Make sure a product ID was actually provided
    if product_id is None:
        return redirect(url_for("home_page"))

    # Guest cart
    if "user_id" not in session:

        guest_cart = session.get("guest_cart", {})

        if product_id in guest_cart:
            guest_cart[product_id] += 1
        else:
            guest_cart[product_id] = 1

        session["guest_cart"] = guest_cart

        return redirect(url_for("cart_page"))

    # Logged-in user's cart
    user_id = session["user_id"]

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    existing = c.execute("""
        SELECT quantity
        FROM Cart_Items
        WHERE user_id = ? AND product_id = ?
    """, (user_id, product_id)).fetchone()

    if existing:
        c.execute("""
            UPDATE Cart_Items
            SET quantity = quantity + 1
            WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id))
    else:
        c.execute("""
            INSERT INTO Cart_Items
            (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (user_id, product_id, 1))

    conn.commit()
    conn.close()

    return redirect(url_for("cart_page"))







@designated_donut.route("/increase_cart", methods=["POST"])
def increase_cart():

    product_id = request.form.get("product_id")

    # Guest
    if "user_id" not in session:

        guest_cart = session.get("guest_cart", {})

        guest_cart[product_id] = guest_cart.get(product_id, 0) + 1

        session["guest_cart"] = guest_cart

        return redirect(url_for("cart_page"))

    # Logged-in user
    user_id = session["user_id"]

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
        UPDATE Cart_Items
        SET quantity = quantity + 1
        WHERE user_id = ? AND product_id = ?
    """, (user_id, product_id))

    conn.commit()
    conn.close()

    return redirect(url_for("cart_page"))




@designated_donut.route("/decrease_cart", methods=["POST"])
def decrease_cart():

    product_id = request.form.get("product_id")

    # Guest
    if "user_id" not in session:

        guest_cart = session.get("guest_cart", {})

        if product_id in guest_cart:

            guest_cart[product_id] -= 1

            if guest_cart[product_id] <= 0:
                del guest_cart[product_id]

        session["guest_cart"] = guest_cart

        return redirect(url_for("cart_page"))

    # Logged-in user
    user_id = session["user_id"]

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    existing = c.execute("""
        SELECT quantity
        FROM Cart_Items
        WHERE user_id = ? AND product_id = ?
    """, (user_id, product_id)).fetchone()

    if existing:

        if existing[0] > 1:
            c.execute("""
                UPDATE Cart_Items
                SET quantity = quantity - 1
                WHERE user_id = ? AND product_id = ?
            """, (user_id, product_id))

        else:
            c.execute("""
                DELETE FROM Cart_Items
                WHERE user_id = ? AND product_id = ?
            """, (user_id, product_id))

    conn.commit()
    conn.close()

    return redirect(url_for("cart_page"))





@designated_donut.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():

    product_id = request.form.get("product_id")

    # Guest
    if "user_id" not in session:

        guest_cart = session.get("guest_cart", {})

        if product_id in guest_cart:
            del guest_cart[product_id]

        session["guest_cart"] = guest_cart

        return redirect(url_for("cart_page"))

    # Logged-in user
    user_id = session["user_id"]

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
        DELETE FROM Cart_Items
        WHERE user_id = ? AND product_id = ?
    """, (user_id, product_id))

    conn.commit()
    conn.close()

    return redirect(url_for("cart_page"))












@designated_donut.route("/checkout", methods=["POST"])
def checkout():

    # Customer must be logged in
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    user_id = session["user_id"]

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Get everything currently in the user's cart
    cart_items = c.execute("""
        SELECT product_id, quantity
        FROM Cart_Items
        WHERE user_id = ?
    """, (user_id,)).fetchall()

    # Make sure there is actually something in the cart
    if not cart_items:
        conn.close()
        return redirect(url_for("cart_page"))


    # Create a new Order ID
    last_order = c.execute("""
        SELECT MAX(order_id)
        FROM Orders
    """).fetchone()

    if last_order[0] is None:
        new_order_id = 1
    else:
        new_order_id = last_order[0] + 1

    # Create the order date
    order_date = datetime.now().strftime("%d/%m/%Y")

    # Create the order
    c.execute("""
        INSERT INTO Orders
        (order_id, user_id, order_date)
        VALUES (?, ?, ?)
    """, (new_order_id, user_id, order_date))

    # Add each cart item to the order
    for product_id, quantity in cart_items:

        c.execute("""
            INSERT INTO Order_Items
            (order_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (new_order_id, product_id, quantity))

    # Now clear the cart
    c.execute("""
        DELETE FROM Cart_Items
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

    # Take the customer to the thank-you page
    return redirect(url_for("thankyou_page"))






@designated_donut.route("/thankyou")
def thankyou_page():

    # Customer must be logged in
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    user_id = session["user_id"]

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

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

    conn.close()

    return render_template(
        "thankyou.html",
        orders=orders
    )



@designated_donut.route('/')
def home_page():
    return render_template('index.html')



@designated_donut.route('/about')
def about_page():
    return render_template('about.html')


@designated_donut.route('/order')
def order_page():

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    products = c.execute("""
        SELECT * FROM Products
    """).fetchall()

    conn.close()

    return render_template("order.html", products=products)








@designated_donut.route("/review")
def review_page():

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

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

    conn.close()

    return render_template(
        "review.html",
        reviews=reviews
    )


@designated_donut.route("/add_review", methods=["POST"])
def add_review():

    if "user_id" not in session:
        return redirect(url_for("login_page"))

    user_id = session["user_id"]

    review_text = request.form.get("review_text")
    rating = request.form.get("rating")
    review_date = request.form.get("review_date")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    last_review = c.execute("""
        SELECT MAX(review_id)
        FROM Reviews
    """).fetchone()

    if last_review[0] is None:
        new_review_id = 10001
    else:
        new_review_id = last_review[0] + 1

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

    conn.commit()
    conn.close()

    return redirect(url_for("review_page"))



@designated_donut.route('/feedback')
def feedback_page():
    return render_template('feedback.html')



if __name__ == '__main__':
    designated_donut.run(debug=True, port=8000)