from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models.repository import Repository

import io
from flask import send_file

app = Flask(__name__)
app.secret_key = 'ваш_секретный_ключ_для_флеш_сообщений'

repo = Repository()


# --- Маршруты (Роуты) ---
@app.route('/')
def index():
    return render_template('index.html', teachers=repo.teachers)


@app.route('/students')
def students():
    return render_template('students.html', students=repo.students)


@app.route('/teachers')
def teachers():
    return render_template('teachers.html', teachers=repo.teachers)


@app.route('/teacher_report/<int:teacher_id>')
def teacher_report(teacher_id):
    """
    Отображает отчет с аналитикой по преподавателю.
    """
    analytics = repo.get_teacher_analytics(teacher_id)

    if not analytics:
        flash('Преподаватель не найден.', 'error')
        return redirect(url_for('teachers'))

    return render_template('teacher_report.html', analytics=analytics)


@app.route('/courses')
def courses():
    return render_template('courses.html', courses=repo.courses, repo=repo)


@app.route('/student/<int:student_id>')
def student_report(student_id):
    student = repo.find_student_by_id(student_id)
    if not student:
        flash('Студент не найден.', 'error')
        return redirect(url_for('students'))

    detailed_history = []
    for entry in student.history:
        course = repo.find_course_by_title(entry.get("course_title"))
        teacher = None
        if course:
            teacher = repo.find_teacher_by_id(course.teacher_id)

        detailed_history.append({
            "course_title": entry.get("course_title"),
            "grade": entry.get("grade"),
            "course_object": course,
            "teacher_object": teacher,
        })

    return render_template('student_report.html', student=student, detailed_history=detailed_history)


# --- МАРШРУТ: ЭКСПОРТ ДАННЫХ ---
@app.route('/export')
def export_data():
    """
    Обрабатывает запросы на экспорт данных в CSV.
    """
    student_id = request.args.get('student_id', type=int)
    export_type = request.args.get('type')

    if not student_id or not export_type:
        flash('Недостаточно параметров для экспорта.', 'error')
        return redirect(url_for('students'))

    if export_type == 'student_report':
        csv_data = repo.export_student_report_to_csv(student_id)
    elif export_type == 'teacher_analytics':
        csv_data = repo.export_teacher_analytics_to_csv(student_id)
    else:
        flash('Некорректный тип экспорта.', 'error')
        return redirect(url_for('students'))

    if not csv_data:
        flash('Данные для отчета не найдены.', 'error')
        return redirect(url_for('students'))

    # Создаем ответ с CSV-данными
    si = io.StringIO(csv_data)
    output = io.BytesIO(si.getvalue().encode('utf-8-sig'))
    output.seek(0)
    return send_file(output,
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name=f"report_{export_type}_{student_id}.csv")


# --- Обработчики форм (POST-запросы) ---
@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form.get('name')
    email = request.form.get('email')
    if name and email:
        repo.add_student(name, email)
        repo.save_to_json()
        flash('Студент успешно добавлен!', 'success')
    else:
        flash('Пожалуйста, заполните все поля.', 'error')
    return redirect(url_for('students'))


@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    name = request.form.get('name')
    spec = request.form.get('specialization')
    if name and spec:
        repo.add_teacher(name, spec)
        repo.save_to_json()
        flash('Преподаватель успешно добавлен!', 'success')
    else:
        flash('Пожалуйста, заполните все поля.', 'error')
    return redirect(url_for('teachers'))


@app.route('/add_course', methods=['POST'])
def add_course():
    title = request.form.get('title')
    topic = request.form.get('topic')
    teacher_id = request.form.get('teacher_id', type=int)

    if title and topic:
        new_course = repo.add_course(title, topic)
        if teacher_id is not None:
            repo.assign_teacher_to_course(new_course.id, teacher_id)
        repo.save_to_json()
        flash(f'Курс "{title}" успешно создан!', 'success')
    else:
        flash('Пожалуйста, заполните все поля.', 'error')
    return redirect(url_for('courses'))


@app.route('/enroll_student', methods=['POST'])
def enroll_student():
    student_id = request.form.get('student_id', type=int)
    course_id = request.form.get('course_id', type=int)

    if student_id and course_id:
        success = repo.enroll_student_in_course(student_id, course_id)
        if success:
            repo.save_to_json()
            flash(f'Студент зачислен на курс.', 'success')
        else:
            flash('Ошибка зачисления. Проверьте правильность ID.', 'error')
    else:
        flash('ID должны быть числами.', 'error')
    return redirect(url_for('courses'))


@app.route('/set_grade', methods=['POST'])
def set_grade():
    student_id = request.form.get('student_id', type=int)
    course_id = request.form.get('course_id', type=int)
    grade = request.form.get('grade', type=int)

    if student_id and course_id and grade and 2 <= grade <= 5:
        course = repo.find_course_by_id(course_id)
        if course and student_id in course.students:
            student = repo.find_student_by_id(student_id)
            student.history.append({
                "course_title": course.title,
                "grade": grade,
                "status": "завершён"
            })
            repo.save_to_json()
            flash(f'Оценка {grade} выставлена.', 'success')
        else:
            flash('Студент не найден на этом курсе.', 'error')
    else:
        flash('Оценка должна быть в диапазоне от 2 до 5.', 'error')
    return redirect(url_for('courses'))


# --- ОБРАБОТЧИКИ: Удаление ---
@app.route('/delete_student/<int:student_id>', methods=['GET', 'POST'])
def delete_student(student_id):
    for course in repo.courses:
        if student_id in course.students:
            course.students.remove(student_id)
    for i, student in enumerate(repo.students):
        if student.id == student_id:
            del repo.students[i]
            break
    repo.save_to_json()
    flash(f'Студент удален.', 'success')
    return redirect(url_for('students'))


@app.route('/delete_teacher/<int:teacher_id>', methods=['GET', 'POST'])
def delete_teacher(teacher_id):
    for course in repo.courses:
        if course.teacher_id == teacher_id:
            course.teacher_id = None
    for i, teacher in enumerate(repo.teachers):
        if teacher.id == teacher_id:
            del repo.teachers[i]
            break
    repo.save_to_json()
    flash(f'Преподаватель удален.', 'success')
    return redirect(url_for('teachers'))


@app.route('/delete_course/<int:course_id>', methods=['GET', 'POST'])
def delete_course(course_id):
    # 1. Сначала находим объект курса
    course = repo.find_course_by_id(course_id)
    if not course:
        flash('Курс не найден.', 'error')
        return redirect(url_for('courses'))

    # 2. Удаляем упоминания о курсе из историй студентов
    for student in repo.students:
        student.history = [e for e in student.history if e.get("course_title") != course.title]

    # 3. Удаляем сам курс из списка курсов
    for i, c in enumerate(repo.courses):
        if c.id == course_id:
            del repo.courses[i]
            break

    repo.save_to_json()
    flash(f'Курс "{course.title}" удален.', 'success')
    return redirect(url_for('courses'))


@app.route('/assign_teacher', methods=['POST'])
def assign_teacher():
    data = request.get_json(silent=True) or {}
    try:
        course_id = int(data.get('course_id'))
        teacher_id = int(data.get('teacher_id'))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Некорректные данные."})

    success = repo.assign_teacher_to_course(course_id, teacher_id)
    if success:
        repo.save_to_json()
        return jsonify({"success": True, "message": "Назначено успешно."})

    return jsonify({"success": False, "message": "Ошибка при назначении."})


if __name__ == '__main__':
    app.run(debug=True)