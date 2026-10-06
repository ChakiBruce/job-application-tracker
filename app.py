"""Command-line menu for the job application tracker."""

from datetime import date

from src.tracker import add_application, get_applications, initialize_database


def read_required(prompt):
    """Keep asking until the user enters a nonempty value."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Please enter a value.")


def add_application_flow():
    """Collect an application and save it to SQLite."""
    company = read_required("Company: ")
    role = read_required("Role: ")

    while True:
        application_date = input("Application date (YYYY-MM-DD, Enter for today): ").strip()
        if not application_date:
            application_date = date.today().isoformat()
        try:
            parsed_date = date.fromisoformat(application_date)
            if parsed_date.isoformat() != application_date:
                raise ValueError
            break
        except ValueError:
            print("Please use a valid date in YYYY-MM-DD format.")

    status = input("Status (Enter for Applied): ").strip() or "Applied"
    add_application(company, role, application_date, status)
    print("Application saved.")


def view_applications():
    """Display applications saved in SQLite."""
    applications = get_applications()
    if not applications:
        print("No applications yet. Choose 1 to add one.")
        return

    for number, application in enumerate(applications, start=1):
        print(f"\n{number}. {application['company']} - {application['role']}")
        print(f"   Date: {application['application_date']}")
        print(f"   Status: {application['status']}")


def main():
    initialize_database()

    print("Job Application Tracker")


    while True:
        print("\n1. Add application\n2. View applications\n3. Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            add_application_flow()
        elif choice == "2":
            view_applications()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Please choose 1, 2, or 3.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")


