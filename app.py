"""Command-line menu for the job application tracker."""

from datetime import date

from src.tracker import initialize_database


def read_required(prompt):
    """Keep asking until the user enters a nonempty value."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Please enter a value.")


def add_application(applications):
    """Collect an application and store it for this session."""
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
    applications.append({
        "company": company,
        "role": role,
        "application_date": application_date,
        "status": status,
    })
    print("Application added for this session.")


def view_applications(applications):
    """Display the applications entered during this session."""
    if not applications:
        print("No applications yet. Choose 1 to add one.")
        return

    for number, application in enumerate(applications, start=1):
        print(f"\n{number}. {application['company']} - {application['role']}")
        print(f"   Date: {application['application_date']}")
        print(f"   Status: {application['status']}")


def main():
    initialize_database()
    applications = []
    print("Job Application Tracker")
    print("Entries are temporary and will be lost when you exit.")

    while True:
        print("\n1. Add application\n2. View applications\n3. Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            add_application(applications)
        elif choice == "2":
            view_applications(applications)
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

