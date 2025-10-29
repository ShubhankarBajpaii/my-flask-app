from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import string

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



#defining Models-------------------------------------------------------------------------------------------------------------------------------------------
class Student(db.Model):
    __tablename__ = 'student'

    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))

    # Relationship (one student → many enrollments)
    enrollments = db.relationship('Enrollment', backref='student', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Student {self.roll_number} - {self.first_name} {self.last_name}>'

class Course(db.Model):
    __tablename__ = 'course'

    course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    course_description = db.Column(db.String(255))

    # Relationship (one course → many enrollments)
    enrollments = db.relationship('Enrollment', backref='course', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Course {self.course_code} - {self.course_name}>'
        
class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    enrollment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    estudent_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    ecourse_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)
    
    # defining relationship---------------
    #course = db.relationship('Course', backref='enrollments')

    def __repr__(self):
        return f'<Enrollment student_id={self.student_id} course_id={self.course_id}>'
#----------------------------------------------------------------------------------------------------------------------------------------------------------




# Adding Routes--------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/')
def home():
    students = Student.query.all()
    return render_template("index.html", students=students)
    
@app.route('/student/create', methods=['GET', 'POST'])
def create_student():
    if request.method == 'GET':
        return render_template("create_student.html")
    
    elif request.method == 'POST':
        roll_number = request.form['roll']
        first_name = request.form['f_name']
        last_name = request.form['l_name']
        
        
        
        existing_student = Student.query.filter_by(roll_number=roll_number).first()
        if existing_student:
            return render_template("error.html", message="Roll number already exists!")
        
        #Adding to new student to student database
        new_student = Student(
        roll_number=roll_number,
        first_name=first_name,
        last_name=last_name)
        
        db.session.add(new_student)
        db.session.flush()
        
        selected_courses = request.form.getlist('courses')
        
        #Adding to enrollment database
        for cid in selected_courses:
            enrollment  = Enrollment(estudent_id = new_student.student_id, ecourse_id = cid)
            db.session.add(enrollment)
        
        
        db.session.commit()
        
        return redirect(url_for('home'))
        
@app.route('/student/<int:student_id>/update', methods=['GET', 'POST'])
def update_student(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'GET':
        return render_template(
            "update_student.html",
            student_id=student.student_id,
            current_roll=student.roll_number,
            current_f_name=student.first_name,
            current_l_name=student.last_name
        )

    elif request.method == 'POST':
        student.first_name = request.form['f_name']
        student.last_name = request.form['l_name']

        # delete all existing enrollments
        Enrollment.query.filter_by(estudent_id=student_id).delete()

        selected_courses = request.form.getlist('courses')
        for cid in selected_courses:
            enrollment = Enrollment(estudent_id=student.student_id, ecourse_id=cid)
            db.session.add(enrollment)

        db.session.commit()
        return redirect(url_for('home'))

@app.route('/student/<int:student_id>/delete', methods=['GET'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)

    db.session.delete(student)  # this also deletes related enrollments because of cascade
    db.session.commit()

    return redirect(url_for('home'))
    
    
@app.route('/student/<int:student_id>', methods=['GET'])
def student_detail(student_id):
    courses, cids = [], []
    student = Student.query.get(student_id)
    enrollments = Enrollment.query.filter_by(estudent_id=student_id).all()
    
    for enrollment in enrollments:
        cids.append(enrollment.ecourse_id[-1])
        
    for cid in cids:
        course = Course.query.filter_by(course_id=cid).first()
        if course:
            courses.append(course)

        
        
    return render_template('student_detail.html', roll_no=student.roll_number, first_name=student.first_name, last_name=student.last_name, courses=courses)
#---------------------------------------------------------------------------------------------------------------------------------------------------------



# Running the app-----------------------------------------------------------------------------------------------------------------------------------------  
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug = True)
