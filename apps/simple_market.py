PRODUCT_FILE = "products.txt"

def add_product_to_market(name, price):
    f = open(PRODUCT_FILE, "a")
    f.write(name + "," + price + "\n")
    f.close()
    return name + " added."

def remove_product_from_market(name):
    f = open(PRODUCT_FILE, "r")
    lines = f.readlines()
    f.close()

    f = open(PRODUCT_FILE, "w")
    for line in lines:
        if line.split(",")[0] != name:
            f.write(line)
    f.close()

    return name + " removed."

def suggest_from_market(product_name):
    f = open(PRODUCT_FILE, "r")
    products = []
    for line in f:
        p = line.strip().split(",")[0]
        if p != product_name:
            products.append(p)
    f.close()
    return products[:3]

def inform_product(name):
    if name == "milk":
        return "Milk is used for drinking and cooking."
    if name == "rice":
        return "Rice is used in meals."
    if name == "apple":
        return "Apple is used for snacks and juices."
    return "No info."

def ask_finished_shopping(ans):
    if ans == "y":
        return "Proceed."
    return "Continue."


def monthly_discount(month):
    if month == "january":
        return "10% off dairy."
    if month == "february":
        return "5% off fruits."
    return "No discount."

def savings(product, old_price, new_price):
    return "You saved " + str(old_price - new_price)

def alternative_product(product):
    if product == "milk":
        return "soy milk"
    if product == "chips":
        return "popcorn"
    return "none"

def time_remaining(hour):
    return str(24 - hour) + " hours left."

def product_packages(product):
    if product == "milk":
        return "1L=20, 2L=35"
    if product == "rice":
        return "1kg=25, 5kg=100"
    return "No packages."

def calculate_receipt(prices):
    return sum(prices)

def choose_payment_method(method):
    return "You chose " + method

def create_user_account(name, ID):
    return name[:3].upper() + ID[-3:]

def checkout_method(choice):
    return "You chose " + choice

def program_card(ans):
    if ans == "yes":
        return "Cashback added"
    return "No card"



# -----------------------------------
# MAIN PROGRAM
# -----------------------------------

def main():
    print("Welcome to the Market")

    print("1. Owner")
    print("2. Customer")
    role = input("Choose: ")

    # ---------------- OWNER ----------------
    if role == "1":
        while True:
            print("\n--- OWNER MENU ---")
            print("1. Add product")
            print("2. Remove product")
            print("3. Suggest")
            print("4. Inform")
            print("5. Exit")
            c = input("Choose: ")

            if c == "1":
                n = input("Name: ")
                p = input("Price: ")
                print(add_product_to_market(n, p))

            elif c == "2":
                n = input("Name: ")
                print(remove_product_from_market(n))

            elif c == "3":
                n = input("Name: ")
                print(suggest_from_market(n))

            elif c == "4":
                n = input("Name: ")
                print(inform_product(n))

            elif c == "5":
                break

    # ---------------- CUSTOMER ----------------
    elif role == "2":
        name = input("Name: ")
        ID = input("ID: ")
        print("Your code:", create_user_account(name, ID))

        cart = []
        prices = []

        while True:
            print("\n--- CUSTOMER MENU ---")
            print("1. Add to cart")
            print("2. Monthly discount")
            print("3. Savings")
            print("4. Alternative")
            print("5. Offer time")
            print("6. Packages")
            print("7. Checkout")
            c = input("Choose: ")

            if c == "1":
                print("Available products:")
                f = open(PRODUCT_FILE, "r")
                content = f.read()
                print(content)
                f.close()

                n = input("Product name: ")

                f = open(PRODUCT_FILE, "r")
                for line in f:
                    p, pr = line.strip().split(",")
                    if p == n:
                        cart.append(p)
                        prices.append(float(pr))
                f.close()

            elif c == "2":
                m = input("Month: ")
                print(monthly_discount(m))

            elif c == "3":
                p = input("Product: ")
                old = float(input("Old price: "))
                new = float(input("New price: "))
                print(savings(p, old, new))

            elif c == "4":
                p = input("Product: ")
                print(alternative_product(p))

            elif c == "5":
                h = int(input("Hour: "))
                print(time_remaining(h))

            elif c == "6":
                p = input("Product: ")
                print(product_packages(p))

            elif c == "7":
                print("Cart:", cart)
                print("Total:", calculate_receipt(prices))

                ans = input("Finished shopping? (y/n): ")
                print(ask_finished_shopping(ans))

                pay = input("Payment method: ")
                print(choose_payment_method(pay))

                card = input("Do you have a card? ")
                print(program_card(card))

                way = input("Delivery or takeaway: ")
                print(checkout_method(way))

                print("Thank you!")
                break


main()

