from flask import Flask, render_template_string, request, redirect, url_for, flash
import json
import os
from datetime import datetime

# --- Student and StudentManager classes (updated for teacher association) ---
class Student:
    def __init__(self, name, age, student_class, roll_number, teacher_username=None):
        self.name = name
        self.age = age
        self.student_class = student_class
        self.roll_number = roll_number
        self.teacher_username = teacher_username

    def to_dict(self):
        return {
            'name': self.name,
            'age': self.age,
            'class': self.student_class,
            'roll_number': self.roll_number,
            'teacher_username': self.teacher_username
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data['name'],
            data['age'],
            data['class'],
            data['roll_number'],
            data.get('teacher_username')
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

    def add_student(self, name, age, student_class, roll_number, teacher_username=None):
        if roll_number in self.students:
            return False, f"Student with roll number {roll_number} already exists!"
        student = Student(name, age, student_class, roll_number, teacher_username)
        self.students[roll_number] = student
        self.save_students()
        self.log_action('add', student)
        return True, f"Student '{name}' added successfully!"

    def remove_student(self, roll_number):
        if roll_number in self.students:
            student = self.students[roll_number]
            del self.students[roll_number]
            self.save_students()
            self.log_action('remove', student)
            return True, f"Student with roll number {roll_number} removed successfully!"
        else:
            return False, f"Student with roll number {roll_number} not found!"

    def edit_student(self, roll_number, name=None, age=None, student_class=None, teacher_username=None):
        if roll_number not in self.students:
            return False, f"Student with roll number {roll_number} not found!"
        student = self.students[roll_number]
        updates = {}
        if name:
            updates['name'] = name
        if age:
            updates['age'] = age
        if student_class:
            updates['class'] = student_class
        if teacher_username is not None:
            updates['teacher_username'] = teacher_username
        for key, value in updates.items():
            setattr(student, key if key != 'class' else 'student_class', value)
        self.save_students()
        self.log_action('edit', student, details=updates)
        return True, "Student updated successfully!"

    def get_student(self, roll_number):
        return self.students.get(roll_number)

    def get_all_students(self, teacher_username=None):
        students = list(self.students.values())
        if teacher_username:
            students = [s for s in students if s.teacher_username == teacher_username]
        return sorted(students, key=lambda s: s.roll_number)

    def view_logs(self, filter_by=None, filter_value=None):
        if not os.path.exists(self.log_filename):
            return []
        with open(self.log_filename, 'r') as f:
            try:
                logs = json.load(f)
            except Exception:
                return []
        filtered_logs = logs
        if filter_by and filter_value:
            if filter_by == 'name':
                filtered_logs = [log for log in logs if log['student'] and log['student']['name'].lower() == filter_value.lower()]
            elif filter_by == 'roll_number':
                filtered_logs = [log for log in logs if log['student'] and str(log['student']['roll_number']) == str(filter_value)]
        return filtered_logs

# --- Teacher and TeacherManager classes ---
class Teacher:
    def __init__(self, username, password, last_password_change=None):
        self.username = username
        self.password = password
        self.last_password_change = last_password_change or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            'username': self.username,
            'password': self.password,
            'last_password_change': self.last_password_change
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data['username'],
            data['password'],
            data.get('last_password_change')
        )

class TeacherManager:
    def __init__(self, filename="teachers.json", log_filename="teacher_log.json"):
        self.filename = filename
        self.log_filename = log_filename
        self.teachers = {}
        self.load_teachers()

    def log_action(self, action, teacher=None, details=None):
        log_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'action': action,
            'teacher': teacher.to_dict() if teacher else None,
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

    def load_teachers(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    self.teachers = {uname: Teacher.from_dict(t) for uname, t in data.items()}
            except Exception as e:
                print(f"Error loading teachers: {e}")
                self.teachers = {}
        else:
            self.teachers = {}

    def save_teachers(self):
        data = {uname: teacher.to_dict() for uname, teacher in self.teachers.items()}
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)

    def add_teacher(self, username, password):
        if username in self.teachers:
            return False, f"Teacher with username {username} already exists!"
        teacher = Teacher(username, password)
        self.teachers[username] = teacher
        self.save_teachers()
        self.log_action('add', teacher)
        return True, f"Teacher '{username}' added successfully!"

    def remove_teacher(self, username):
        if username in self.teachers:
            teacher = self.teachers[username]
            del self.teachers[username]
            self.save_teachers()
            self.log_action('remove', teacher)
            return True, f"Teacher '{username}' removed successfully!"
        else:
            return False, f"Teacher with username {username} not found!"

    def edit_teacher(self, username, new_password=None):
        if username not in self.teachers:
            return False, f"Teacher with username {username} not found!"
        teacher = self.teachers[username]
        updates = {}
        if new_password and new_password != teacher.password:
            teacher.password = new_password
            teacher.last_password_change = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updates['password'] = new_password
            updates['last_password_change'] = teacher.last_password_change
        self.save_teachers()
        if updates:
            self.log_action('edit_password', teacher, details=updates)
        return True, "Teacher updated successfully!"

    def get_teacher(self, username):
        return self.teachers.get(username)

    def get_all_teachers(self):
        return sorted(self.teachers.values(), key=lambda t: t.username)

    def view_logs(self):
        if not os.path.exists(self.log_filename):
            return []
        with open(self.log_filename, 'r') as f:
            try:
                logs = json.load(f)
            except Exception:
                return []
        return logs

# --- Flask App ---
app = Flask(__name__)
app.secret_key = 'student-info-secret'
manager = StudentManager(os.path.join(os.path.dirname(__file__), 'students.json'), os.path.join(os.path.dirname(__file__), 'master_log.json'))
teacher_manager = TeacherManager(os.path.join(os.path.dirname(__file__), 'teachers.json'), os.path.join(os.path.dirname(__file__), 'teacher_log.json'))

# --- HTML Templates ---
layout = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Student Info System</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #e6f2ff; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 2em; border-radius: 8px; box-shadow: 0 2px 8px #ccc; }
        h1, h2 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 1em; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background: #eee; }
        .actions a { margin-right: 8px; }
        .msg { color: green; }
        .err { color: red; }
        form { margin-bottom: 1em; }
        input[type=text], input[type=number], input[type=password] { padding: 6px; width: 95%; }
        input[type=submit], button, .btn {
            padding: 8px 18px;
            border: none;
            border-radius: 5px;
            background: linear-gradient(90deg, #2196f3 0%, #21cbf3 100%);
            color: #fff;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(33,150,243,0.08);
            transition: background 0.2s, box-shadow 0.2s;
            text-decoration: none;
            display: inline-block;
        }
        input[type=submit]:hover, button:hover, .btn:hover {
            background: linear-gradient(90deg, #1976d2 0%, #00bcd4 100%);
            box-shadow: 0 4px 8px rgba(33,150,243,0.15);
        }
        .btn-cancel, button[type="button"] {
            background: #f0f0f0;
            color: #333;
            border: 1px solid #ccc;
        }
        .btn-cancel:hover, button[type="button"]:hover {
            background: #e0e0e0;
            color: #111;
        }
        .nav { margin-bottom: 1em; }
        .nav a { margin-right: 16px; }
        .nav .btn { margin-right: 16px; }
    </style>
</head>
<body>
<div class="container">
    <div class="nav">
        <a href="{{ url_for('index') }}" class="btn">Home</a>
        <a href="{{ url_for('add_student') }}" class="btn">Add Student</a>
        <a href="{{ url_for('view_logs') }}" class="btn">Master Log</a>
        <a href="{{ url_for('principal_dashboard') }}" class="btn">Principal Dashboard</a>
    </div>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="{{ category }}">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    CONTENT_BLOCK
</div>
</body>
</html>
'''

# ... (student templates unchanged)

principal_content = '''
<h1>Principal Dashboard - Teachers</h1>
<a href="{{ url_for('add_teacher') }}"><button>Add Teacher</button></a>
<table>
    <tr><th>Username</th><th>Password</th><th>Last Password Change</th><th>Actions</th></tr>
    {% for teacher in teachers %}
    <tr>
        <td>{{ teacher.username }}</td>
        <td>{{ teacher.password }}</td>
        <td>{{ teacher.last_password_change }}</td>
        <td class="actions">
            <a href="{{ url_for('edit_teacher', username=teacher.username) }}">Edit</a>
            <a href="{{ url_for('remove_teacher', username=teacher.username) }}" onclick="return confirm('Remove this teacher?');">Remove</a>
        </td>
    </tr>
    {% endfor %}
</table>
'''

add_teacher_content = '''
<h1>Add Teacher</h1>
<form method="post">
    <label>Username:<br><input type="text" name="username" required></label><br><br>
    <label>Password:<br><input type="password" name="password" required></label><br><br>
    <input type="submit" value="Add Teacher">
    <a href="{{ url_for('principal_dashboard') }}"><button type="button">Cancel</button></a>
</form>
'''

edit_teacher_content = '''
<h1>Edit Teacher - {{ teacher.username }}</h1>
<form method="post">
    <label>New Password:<br><input type="password" name="password" value="{{ teacher.password }}" required></label><br><br>
    <input type="submit" value="Update Password">
    <a href="{{ url_for('principal_dashboard') }}"><button type="button">Cancel</button></a>
</form>
<p>Last Password Change: {{ teacher.last_password_change }}</p>
'''

# --- Student templates (unchanged) ---
index_content = '''
<h1>Student List</h1>
<form method="get" style="margin-bottom:1em;">
    <label>Filter by Teacher:
        <select name="teacher_username">
            <option value="">All</option>
            {% for teacher in teachers %}
                <option value="{{ teacher.username }}" {% if teacher.username == selected_teacher %}selected{% endif %}>{{ teacher.username }}</option>
            {% endfor %}
        </select>
    </label>
    <input type="submit" value="Filter">
</form>
{% if students %}
<table>
    <tr><th>Roll No.</th><th>Name</th><th>Age</th><th>Class</th><th>Teacher</th><th>Actions</th></tr>
    {% for student in students %}
    <tr>
        <td>{{ student.roll_number }}</td>
        <td>{{ student.name }}</td>
        <td>{{ student.age }}</td>
        <td>{{ student.student_class }}</td>
        <td>{{ student.teacher_username or '' }}</td>
        <td class="actions">
            <a href="{{ url_for('view_student', roll_number=student.roll_number) }}">View</a>
            <a href="{{ url_for('edit_student', roll_number=student.roll_number) }}">Edit</a>
            <a href="{{ url_for('remove_student', roll_number=student.roll_number) }}" onclick="return confirm('Remove this student?');">Remove</a>
        </td>
    </tr>
    {% endfor %}
</table>
{% else %}
<p>No students found.</p>
{% endif %}
'''

add_edit_content = '''
<h1>{{ 'Edit' if edit else 'Add' }} Student</h1>
<form method="post">
    <label>Name:<br><input type="text" name="name" value="{{ student.name if student else '' }}" required></label><br><br>
    <label>Age:<br><input type="number" name="age" value="{{ student.age if student else '' }}" required></label><br><br>
    <label>Class:<br><input type="text" name="class" value="{{ student.student_class if student else '' }}" required></label><br><br>
    <label>Roll Number:<br><input type="text" name="roll_number" value="{{ student.roll_number if student else '' }}" {% if edit %}readonly{% endif %} required></label><br><br>
    <label>Class Teacher:<br>
        <select name="teacher_username">
            <option value="">None</option>
            {% for teacher in teachers %}
                <option value="{{ teacher.username }}" {% if student and teacher.username == student.teacher_username %}selected{% endif %}>{{ teacher.username }}</option>
            {% endfor %}
        </select>
    </label><br><br>
    <input type="submit" value="{{ 'Update' if edit else 'Add' }} Student">
    <a href="{{ url_for('index') }}"><button type="button">Cancel</button></a>
</form>
'''

view_content = '''
<h1>Student Details</h1>
{% if student %}
<table>
    <tr><th>Name</th><td>{{ student.name }}</td></tr>
    <tr><th>Age</th><td>{{ student.age }}</td></tr>
    <tr><th>Class</th><td>{{ student.student_class }}</td></tr>
    <tr><th>Roll Number</th><td>{{ student.roll_number }}</td></tr>
</table>
<a href="{{ url_for('edit_student', roll_number=student.roll_number) }}">Edit</a>
<a href="{{ url_for('remove_student', roll_number=student.roll_number) }}" onclick="return confirm('Remove this student?');">Remove</a>
<a href="{{ url_for('index') }}">Back to List</a>
{% else %}
<p>Student not found.</p>
{% endif %}
'''

log_content = '''
<h1>Master Log</h1>
<form method="get" style="margin-bottom:1em;">
    <label>Filter by Name: <input type="text" name="name" value="{{ request.args.get('name', '') }}"></label>
    <label>Filter by Roll Number: <input type="text" name="roll_number" value="{{ request.args.get('roll_number', '') }}"></label>
    <input type="submit" value="Filter">
    <a href="{{ url_for('view_logs') }}"><button type="button">Clear</button></a>
</form>
{% if logs %}
<table>
    <tr><th>Timestamp</th><th>Action</th><th>Name</th><th>Roll No.</th><th>Details</th></tr>
    {% for log in logs %}
    <tr>
        <td>{{ log.timestamp }}</td>
        <td>{{ log.action }}</td>
        <td>{{ log.student.name if log.student else '' }}</td>
        <td>{{ log.student.roll_number if log.student else '' }}</td>
        <td>{{ log.details if log.details else '' }}</td>
    </tr>
    {% endfor %}
</table>
{% else %}
<p>No logs found.</p>
{% endif %}
'''

# --- Flask Routes ---
@app.route('/')
def index():
    selected_teacher = request.args.get('teacher_username', '')
    students = manager.get_all_students(teacher_username=selected_teacher if selected_teacher else None)
    teachers = teacher_manager.get_all_teachers()
    page = layout.replace('CONTENT_BLOCK', index_content)
    return render_template_string(page, students=students, teachers=teachers, selected_teacher=selected_teacher)

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    teachers = teacher_manager.get_all_teachers()
    if request.method == 'POST':
        name = request.form['name'].strip()
        age = request.form['age'].strip()
        student_class = request.form['class'].strip()
        roll_number = request.form['roll_number'].strip()
        teacher_username = request.form.get('teacher_username') or None
        if not (name and age.isdigit() and student_class and roll_number):
            flash('All fields are required and age must be a number.', 'err')
            page = layout.replace('CONTENT_BLOCK', add_edit_content)
            return render_template_string(page, edit=False, student=None, teachers=teachers)
        success, msg = manager.add_student(name, int(age), student_class, roll_number, teacher_username)
        flash(msg, 'msg' if success else 'err')
        if success:
            return redirect(url_for('index'))
    page = layout.replace('CONTENT_BLOCK', add_edit_content)
    return render_template_string(page, edit=False, student=None, teachers=teachers)

@app.route('/edit/<roll_number>', methods=['GET', 'POST'])
def edit_student(roll_number):
    teachers = teacher_manager.get_all_teachers()
    student = manager.get_student(roll_number)
    if not student:
        flash('Student not found.', 'err')
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name'].strip()
        age = request.form['age'].strip()
        student_class = request.form['class'].strip()
        teacher_username = request.form.get('teacher_username') or None
        if not (name and age.isdigit() and student_class):
            flash('All fields are required and age must be a number.', 'err')
            page = layout.replace('CONTENT_BLOCK', add_edit_content)
            return render_template_string(page, edit=True, student=student, teachers=teachers)
        success, msg = manager.edit_student(roll_number, name, int(age), student_class, teacher_username)
        flash(msg, 'msg' if success else 'err')
        if success:
            return redirect(url_for('index'))
    page = layout.replace('CONTENT_BLOCK', add_edit_content)
    return render_template_string(page, edit=True, student=student, teachers=teachers)

@app.route('/remove/<roll_number>')
def remove_student(roll_number):
    success, msg = manager.remove_student(roll_number)
    flash(msg, 'msg' if success else 'err')
    return redirect(url_for('index'))

@app.route('/view/<roll_number>')
def view_student(roll_number):
    student = manager.get_student(roll_number)
    page = layout.replace('CONTENT_BLOCK', view_content)
    return render_template_string(page, student=student)

@app.route('/logs')
def view_logs():
    name = request.args.get('name', '').strip()
    roll_number = request.args.get('roll_number', '').strip()
    filter_by = None
    filter_value = None
    if name:
        filter_by = 'name'
        filter_value = name
    elif roll_number:
        filter_by = 'roll_number'
        filter_value = roll_number
    logs = manager.view_logs(filter_by, filter_value)
    # Convert logs to objects for template
    class LogObj:
        def __init__(self, d):
            self.timestamp = d['timestamp']
            self.action = d['action']
            self.student = type('S', (), d['student']) if d['student'] else None
            self.details = d['details']
    logs = [LogObj(l) for l in logs]
    page = layout.replace('CONTENT_BLOCK', log_content)
    return render_template_string(page, logs=logs, request=request)

# --- Principal Dashboard routes ---
@app.route('/principal')
def principal_dashboard():
    teachers = teacher_manager.get_all_teachers()
    page = layout.replace('CONTENT_BLOCK', principal_content)
    return render_template_string(page, teachers=teachers)

@app.route('/principal/add', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not (username and password):
            flash('All fields are required.', 'err')
            page = layout.replace('CONTENT_BLOCK', add_teacher_content)
            return render_template_string(page)
        success, msg = teacher_manager.add_teacher(username, password)
        flash(msg, 'msg' if success else 'err')
        if success:
            return redirect(url_for('principal_dashboard'))
    page = layout.replace('CONTENT_BLOCK', add_teacher_content)
    return render_template_string(page)

@app.route('/principal/edit/<username>', methods=['GET', 'POST'])
def edit_teacher(username):
    teacher = teacher_manager.get_teacher(username)
    if not teacher:
        flash('Teacher not found.', 'err')
        return redirect(url_for('principal_dashboard'))
    if request.method == 'POST':
        password = request.form['password'].strip()
        if not password:
            flash('Password is required.', 'err')
            page = layout.replace('CONTENT_BLOCK', edit_teacher_content)
            return render_template_string(page, teacher=teacher)
        success, msg = teacher_manager.edit_teacher(username, password)
        flash(msg, 'msg' if success else 'err')
        if success:
            return redirect(url_for('principal_dashboard'))
    page = layout.replace('CONTENT_BLOCK', edit_teacher_content)
    return render_template_string(page, teacher=teacher)

@app.route('/principal/remove/<username>')
def remove_teacher(username):
    success, msg = teacher_manager.remove_teacher(username)
    flash(msg, 'msg' if success else 'err')
    return redirect(url_for('principal_dashboard'))

if __name__ == '__main__':
    app.run(debug=True) 