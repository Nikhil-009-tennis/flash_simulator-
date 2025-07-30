import json
import os
from datetime import datetime

class Student:
    def __init__(self, name, age, student_class, roll_number):
        self.name = name
        self.age = age
        self.student_class = student_class
        self.roll_number = roll_number

    def to_dict(self):
        return {
            'name': self.name,
            'age': self.age,
            'class': self.student_class,
            'roll_number': self.roll_number
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data['name'],
            data['age'],
            data['class'],
            data['roll_number']
        )

class StudentManager:
    def __init__(self, filename="students.json", log_filename="master_log.json"):
        self.filename = filename
        self.log_filename = log_filename
        self.students = {}
        self.load_students()

    def log_action(self, action, student=None, details=None):
        log_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'action': action,
            'student': student.to_dict() if student else None,
            'details': details
        }
        logs = []
        if os.path.exists(self.log_filename):
            with open(self.log_filename, 'r') as f:
                try:
                    logs = json.load(f)
                except Exception:
                    logs = []
        logs.append(log_entry)
        with open(self.log_filename, 'w') as f:
            json.dump(logs, f, indent=2)

    def load_students(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    self.students = {roll: Student.from_dict(stud) for roll, stud in data.items()}
            except Exception as e:
                print(f"Error loading students: {e}")
                self.students = {}
        else:
            self.students = {}

    def save_students(self):
        data = {roll: student.to_dict() for roll, student in self.students.items()}
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)

    def add_student(self, name, age, student_class, roll_number):
        if roll_number in self.students:
            print(f"Student with roll number {roll_number} already exists!")
            return False
        student = Student(name, age, student_class, roll_number)
        self.students[roll_number] = student
        self.save_students()
        self.log_action('add', student)
        print(f"Student '{name}' added successfully!")
        return True

    def remove_student(self, roll_number):
        if roll_number in self.students:
            student = self.students[roll_number]
            del self.students[roll_number]
            self.save_students()
            self.log_action('remove', student)
            print(f"Student with roll number {roll_number} removed successfully!")
            return True
        else:
            print(f"Student with roll number {roll_number} not found!")
            return False

    def edit_student(self, roll_number):
        if roll_number not in self.students:
            print(f"Student with roll number {roll_number} not found!")
            return False
        student = self.students[roll_number]
        print(f"\nEditing student: {student.name} (Roll: {student.roll_number})")
        print("Leave blank to keep current value.")
        new_name = input(f"Name ({student.name}): ").strip()
        new_age = input(f"Age ({student.age}): ").strip()
        new_class = input(f"Class ({student.student_class}): ").strip()
        updates = {}
        if new_name:
            updates['name'] = new_name
        if new_age:
            try:
                updates['age'] = int(new_age)
            except ValueError:
                print("Invalid age. Keeping previous value.")
        if new_class:
            updates['class'] = new_class
        for key, value in updates.items():
            setattr(student, key if key != 'class' else 'student_class', value)
        self.save_students()
        self.log_action('edit', student, details=updates)
        print("Student updated successfully!")
        return True

    def display_all_students(self):
        if not self.students:
            print("No students found.")
            return
        print(f"\n{'='*60}")
        print(f"STUDENT LIST - {len(self.students)} students")
        print(f"{'='*60}")
        print(f"{'Roll No.':<10} | {'Name':<20} | {'Age':<5} | {'Class':<10}")
        print(f"{'-'*60}")
        for roll, student in sorted(self.students.items()):
            print(f"{roll:<10} | {student.name:<20} | {student.age:<5} | {student.student_class:<10}")

    def display_student(self, roll_number):
        if roll_number in self.students:
            student = self.students[roll_number]
            print(f"\n{'='*40}")
            print(f"Name: {student.name}")
            print(f"Age: {student.age}")
            print(f"Class: {student.student_class}")
            print(f"Roll Number: {student.roll_number}")
            print(f"{'='*40}")
            self.log_action('view', student)
        else:
            print(f"Student with roll number {roll_number} not found!")

    def get_roll_numbers(self):
        return sorted(self.students.keys())

    def view_logs(self, filter_by=None, filter_value=None):
        if not os.path.exists(self.log_filename):
            print("No logs found.")
            return
        with open(self.log_filename, 'r') as f:
            try:
                logs = json.load(f)
            except Exception as e:
                print(f"Error reading logs: {e}")
                return
        filtered_logs = logs
        if filter_by and filter_value:
            if filter_by == 'name':
                filtered_logs = [log for log in logs if log['student'] and log['student']['name'].lower() == filter_value.lower()]
            elif filter_by == 'roll_number':
                filtered_logs = [log for log in logs if log['student'] and str(log['student']['roll_number']) == str(filter_value)]
        if not filtered_logs:
            print("No logs found for the given filter.")
            return
        print(f"\n{'='*60}")
        print(f"MASTER LOGS ({len(filtered_logs)} entries)")
        print(f"{'='*60}")
        for log in filtered_logs:
            print(f"[{log['timestamp']}] {log['action'].upper()} - {log['student'] if log['student'] else ''} {log['details'] if log['details'] else ''}")


def display_menu():
    print("\n" + "="*50)
    print("         STUDENT INFO SYSTEM")
    print("="*50)
    print("1. Add Student")
    print("2. Remove Student")
    print("3. Edit Student")
    print("4. Display All Students")
    print("5. Display Specific Student")
    print("6. View Master Log")
    print("7. Search Log by Student Name")
    print("8. Search Log by Roll Number")
    print("9. Exit")
    print("="*50)

def get_student_input():
    name = input("Enter name: ").strip()
    if not name:
        print("Name is required!")
        return None
    age = input("Enter age: ").strip()
    if not age.isdigit():
        print("Age must be a number!")
        return None
    student_class = input("Enter class: ").strip()
    if not student_class:
        print("Class is required!")
        return None
    roll_number = input("Enter roll number: ").strip()
    if not roll_number:
        print("Roll number is required!")
        return None
    return name, int(age), student_class, roll_number

def main():
    manager = StudentManager()
    while True:
        display_menu()
        choice = input("\nEnter your choice (1-9): ").strip()
        if choice == '1':
            print("\n--- ADD NEW STUDENT ---")
            student_data = get_student_input()
            if student_data:
                name, age, student_class, roll_number = student_data
                manager.add_student(name, age, student_class, roll_number)
        elif choice == '2':
            print("\n--- REMOVE STUDENT ---")
            manager.display_all_students()
            roll_number = input("Enter roll number to remove: ").strip()
            if roll_number:
                manager.remove_student(roll_number)
        elif choice == '3':
            print("\n--- EDIT STUDENT ---")
            manager.display_all_students()
            roll_number = input("Enter roll number to edit: ").strip()
            if roll_number:
                manager.edit_student(roll_number)
        elif choice == '4':
            manager.display_all_students()
        elif choice == '5':
            roll_number = input("Enter roll number to display: ").strip()
            if roll_number:
                manager.display_student(roll_number)
        elif choice == '6':
            manager.view_logs()
        elif choice == '7':
            name = input("Enter student name to filter logs: ").strip()
            if name:
                manager.view_logs(filter_by='name', filter_value=name)
        elif choice == '8':
            roll_number = input("Enter roll number to filter logs: ").strip()
            if roll_number:
                manager.view_logs(filter_by='roll_number', filter_value=roll_number)
        elif choice == '9':
            print("\nSaving data before exit...")
            manager.save_students()
            print("Thank you for using Student Info System!")
            break
        else:
            print("Invalid choice! Please enter a number between 1 and 9.")
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
