import streamlit as st

CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Other"]


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def init_state():
    """Create the data we keep while the app is running."""
    if "expenses" not in st.session_state:
        st.session_state.expenses = []      # list of dictionaries
    if "next_id" not in st.session_state:
        st.session_state.next_id = 1        # unique id for every expense
    if "flash" not in st.session_state:
        st.session_state.flash = None       # (type, message) shown once


# ---------------------------------------------------------------------------
# Data logic (callbacks run BEFORE the page redraws, so stats update instantly)
# ---------------------------------------------------------------------------
def add_expense():
    """Validate the form values and add a new expense dictionary to the list."""
    name = st.session_state.form_name.strip()
    amount = st.session_state.form_amount
    category = st.session_state.form_category
    date = st.session_state.form_date

    if name == "":
        st.session_state.flash = ("error", "Expense name cannot be empty.")
    elif amount <= 0:
        st.session_state.flash = ("error", "Amount must be greater than 0.")
    else:
        expense = {
            "id": st.session_state.next_id,
            "name": name,
            "amount": float(amount),
            "category": category,
            "date": str(date),
        }
        st.session_state.expenses.append(expense)
        st.session_state.next_id += 1
        st.session_state.flash = (
            "success",
            "Expense '" + name + "' added successfully!",
        )


def delete_expense(expense_id):
    """Remove the expense with the given id from the list."""
    for expense in st.session_state.expenses:
        if expense["id"] == expense_id:
            st.session_state.expenses.remove(expense)
            st.session_state.flash = (
                "success",
                "Expense '" + expense["name"] + "' deleted.",
            )
            break


# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------
def get_total(expenses):
    total = 0.0
    for expense in expenses:
        total += expense["amount"]
    return total


def get_highest(expenses):
    """Return the expense dictionary with the largest amount (or None)."""
    highest = None
    for expense in expenses:
        if highest is None or expense["amount"] > highest["amount"]:
            highest = expense
    return highest


def get_category_totals(expenses):
    """Return a dictionary like {'Food': 120.0, 'Travel': 50.0, ...}."""
    totals = {}
    for category in CATEGORIES:
        totals[category] = 0.0
    for expense in expenses:
        totals[expense["category"]] += expense["amount"]
    return totals


def apply_filters(expenses, search_text, category, min_amount, max_amount):
    """Return only the expenses that match ALL filters."""
    results = []
    for expense in expenses:
        if search_text.strip() != "":
            if search_text.strip().lower() not in expense["name"].lower():
                continue
        if category != "All" and expense["category"] != category:
            continue
        if expense["amount"] < min_amount or expense["amount"] > max_amount:
            continue
        results.append(expense)
    return results


# ---------------------------------------------------------------------------
# UI sections
# ---------------------------------------------------------------------------
def show_flash():
    """Show a one-time message set by add/delete callbacks."""
    flash = st.session_state.flash
    if flash is not None:
        kind, message = flash
        if kind == "success":
            st.success(message)
        elif kind == "warning":
            st.warning(message)
        else:
            st.error(message)
        st.session_state.flash = None


def show_form():
    st.header("Add Expense")
    with st.form("expense_form", clear_on_submit=True):
        st.text_input("Expense Name", key="form_name")
        st.number_input("Amount", min_value=0.0, step=1.0, format="%.2f",
                        key="form_amount")
        st.selectbox("Category", CATEGORIES, key="form_category")
        st.date_input("Date", key="form_date")
        st.form_submit_button("Add Expense", on_click=add_expense)


def show_dashboard(expenses):
    st.header("Dashboard Summary")
    highest = get_highest(expenses)
    highest_value = 0.0
    if highest is not None:
        highest_value = highest["amount"]

    st.metric("Total Expenses", "{:,.2f}".format(get_total(expenses)))
    st.metric("Total Transactions", len(expenses))
    st.metric("Highest Expense", "{:,.2f}".format(highest_value))


def show_sidebar(expenses):
    """Draw the sidebar filters and return the chosen values."""
    st.sidebar.header("Search & Filters")

    search_text = st.sidebar.text_input("Search Expense by Name")
    category = st.sidebar.selectbox("Category", ["All"] + CATEGORIES)

    highest = get_highest(expenses)
    top = 100.0
    if highest is not None and highest["amount"] > top:
        top = float(highest["amount"])

    min_amount, max_amount = st.sidebar.slider(
        "Amount Range", min_value=0.0, max_value=top, value=(0.0, top)
    )
    return search_text, category, min_amount, max_amount


def show_records(all_expenses, filtered):
    st.header("Expense Records")

    if len(all_expenses) == 0:
        st.warning("No expenses available. Add your first expense above.")
        return
    if len(filtered) == 0:
        st.warning("No expenses match the current filters.")
        return

    rows = []
    for expense in filtered:
        rows.append({
            "Expense Name": expense["name"],
            "Amount": expense["amount"],
            "Category": expense["category"],
            "Date": expense["date"],
        })
    st.dataframe(rows, use_container_width=True)
    st.success("Showing " + str(len(filtered)) + " of "
               + str(len(all_expenses)) + " expense(s).")

    st.subheader("Delete an Expense")
    for expense in filtered:
        label = ("Delete: " + expense["name"] + " | "
                 + "{:,.2f}".format(expense["amount"]) + " | "
                 + expense["category"] + " | " + expense["date"])
        st.button(label, key="delete_" + str(expense["id"]),
                  on_click=delete_expense, args=(expense["id"],))


def show_extra_features(expenses):
    st.header("Additional Insights")

    if len(expenses) == 0:
        st.warning("No records available for analysis.")
        return

    st.subheader("Highest Expense")
    highest = get_highest(expenses)
    st.success("{} - {:,.2f} ({}, {})".format(
        highest["name"], highest["amount"], highest["category"], highest["date"]))

    st.subheader("Total Number of Transactions")
    st.success(str(len(expenses)) + " transaction(s) recorded.")

    st.subheader("Category-wise Total Expenses")
    totals = get_category_totals(expenses)
    rows = []
    for category, total in totals.items():
        rows.append({"Category": category, "Total": total})
        if total == 0:
            continue
    st.dataframe(rows, use_container_width=True)

    empty = []
    for category, total in totals.items():
        if total == 0:
            empty.append(category)
    if len(empty) > 0:
        st.warning("No spending yet in: " + ", ".join(empty))

def main():
    init_state()
    expenses = st.session_state.expenses

    st.title("Personal Expense Tracker")

    show_form()
    show_flash()

    show_dashboard(expenses)

    search_text, category, min_amount, max_amount = show_sidebar(expenses)
    filtered = apply_filters(expenses, search_text, category,
                             min_amount, max_amount)

    show_records(expenses, filtered)
    show_extra_features(expenses)


main()