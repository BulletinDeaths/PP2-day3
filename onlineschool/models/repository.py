import json, os
from .student import Student
from .teacher import Teacher
from .course import Course
from .module import Module
from .lesson import Lesson
from .homework import Homework, HomeworkGrade
import csv
import io


class Repository:
    def __init__(self):
        self.next_ids = {
            "student": 1,
            "teacher": 1,
            "course": 1,
            "module": 1,
            "lesson": 1,
            "homework": 1,
            "homework_grade": 1
        }

        self.students = []
        self.teachers = []
        self.courses = []
        self.modules = []
        self.lessons = []
        self.homeworks = []
        self.homework_grades = []

        self.load_from_json()

    # --- Вспомогательные методы для генерации ID ---
    def _next_module_id(self):
        return max([m.id for m in self.modules], default=self.next_ids.get('module', 0)) + 1

    def _next_lesson_id(self):
        return max([l.id for l in self.lessons], default=self.next_ids.get('lesson', 0)) + 1

    def _next_homework_id(self):
        return max([hw.id for hw in self.homeworks], default=self.next_ids.get('homework', 0)) + 1

    def _next_homework_grade_id(self):
        return max([hg.id for hg in self.homework_grades], default=self.next_ids.get('homework_grade', 0)) + 1

    # --- Методы ДОБАВЛЕНИЯ ---
    def add_student(self, name, email):
        new_student = Student(self.next_ids['student'], name, email)
        self.students.append(new_student)
        self.next_ids['student'] += 1
        self.save_to_json()

    def add_teacher(self, name, specialization):
        new_teacher = Teacher(self.next_ids['teacher'], name, specialization)
        self.teachers.append(new_teacher)
        self.next_ids['teacher'] += 1
        self.save_to_json()

    def add_course(self, title, topic):
        """
        Создает новый курс, используя следующий доступный ID из next_ids,
        добавляет его в список и увеличивает счетчик.
        """
        new_id = self.next_ids['course']
        from .course import Course
        new_course = Course(course_id=new_id, title=title, topic=topic)

        self.courses.append(new_course)
        self.next_ids['course'] += 1
        self.save_to_json()
        return new_course

    # --- Вспомогательные методы поиска ---
    def find_student_by_id(self, student_id):
        """Находит студента по его ID."""
        return next((s for s in self.students if s.id == student_id), None)

    def find_teacher_by_id(self, teacher_id):
        """Находит преподавателя по его ID."""
        return next((t for t in self.teachers if t.id == teacher_id), None)

    def find_course_by_title(self, title):
        """Находит курс по его названию."""
        return next((c for c in self.courses if c.title == title), None)

    def find_course_by_id(self, course_id):
        """Находит курс по его ID."""
        return next((c for c in self.courses if c.id == course_id), None)

    # --- Методы УПРАВЛЕНИЯ СВЯЗЯМИ ---
    def assign_teacher_to_course(self, course_id, teacher_id):
        course = self.find_course_by_id(course_id)
        teacher = self.find_teacher_by_id(teacher_id) if teacher_id else None

        if course:
            course.teacher_id = teacher.id if teacher else None
            return True
        return False

    def enroll_student_in_course(self, student_id, course_id):
        course = self.find_course_by_id(course_id)
        student_exists = self.find_student_by_id(student_id) is not None

        if course and student_exists and student_id not in course.students:
            course.students.append(student_id)
            return True
        return False

    # --- НОВЫЕ МЕТОДЫ ДЛЯ МОДУЛЕЙ И УРОКОВ ---
    def add_module_to_course(self, course_id, title):
        course = self.find_course_by_id(course_id)
        if not course:
            return False, "Курс не найден"

        new_module = Module(self._next_module_id(), title, course_id)
        self.modules.append(new_module)
        course.add_module(new_module.id)
        self.save_to_json()
        return True, new_module

    def add_lesson_to_module(self, module_id, title):
        module = next((m for m in self.modules if m.id == module_id), None)
        if not module:
            return False, "Модуль не найден"

        new_lesson = Lesson(self._next_lesson_id(), title, module_id)
        self.lessons.append(new_lesson)
        module.add_lesson(new_lesson.id)
        self.save_to_json()
        return True, new_lesson

        # --- НОВЫЕ МЕТОДЫ ДЛЯ ДОМАШНИХ ЗАДАНИЙ ---
    def add_homework_to_lesson(self, lesson_id, description, due_date):
        """
        Добавляет домашнее задание к уроку.
        """
        new_hw = Homework(self._next_homework_id(), lesson_id, description, due_date)
        self.homeworks.append(new_hw)
        self.save_to_json()
        return True, new_hw

    def set_grade_for_homework(self, student_id, homework_id, grade):
        """
        Выставляет оценку студенту за конкретное домашнее задание.
        """
        new_grade = HomeworkGrade(
            id=self._next_homework_grade_id(),
            student_id=student_id,
            homework_id=homework_id,
            grade=grade
        )
        self.homework_grades.append(new_grade)
        self.save_to_json()
        return True

    # --- МЕТОД ВЫСТАВЛЕНИЯ ИТОГОВОЙ ОЦЕНКИ ---
    def set_grade_for_student_in_course(self, student_id, course_id, grade):
        course = self.find_course_by_id(course_id)
        student = self.find_student_by_id(student_id)

        if not (course and student and student_id in course.students):
            return False

        hw_grades = [hg for hg in self.homework_grades if hg.student_id == student_id and hg.lesson_id in
                     [l.id for l in self.lessons if l.module_id in
                      [m.id for m in self.modules if m.course_id == course.id]]]

        if hw_grades:
            avg_hw_grade = sum(hg.grade for hg in hw_grades) / len(hw_grades)
            final_grade = (grade + avg_hw_grade) / 2
            grade = int(-(-final_grade // 1))

        history_entry = next((e for e in student.history if e.get("course_title") == course.title), None)
        if history_entry:
            history_entry["grade"] = grade
            history_entry["status"] = "завершён"
        else:
            student.history.append({
                "course_title": course.title,
                "grade": grade,
                "status": "завершён"
            })

        self.save_to_json()
        return True

    def get_teacher_analytics(self, teacher_id):
        """
        Собирает аналитику по преподавателю.
        Возвращает словарь с данными или None, если преподаватель не найден.
        """
        teacher = self.find_teacher_by_id(teacher_id)
        if not teacher:
            return None

        # Находим все курсы этого преподавателя
        teacher_courses = [c for c in self.courses if c.teacher_id == teacher_id]

        # 1. Количество активных курсов
        active_courses = [c for c in teacher_courses if c.status == "активен"]
        num_active_courses = len(active_courses)

        # 2. Средняя успеваемость и список завершенных курсов с оценками
        completed_courses_data = []
        all_grades = []

        for course in teacher_courses:
            if course.status == "завершён":
                course_grades = []
                for student_id in course.students:
                    student = self.find_student_by_id(student_id)
                    entry = next((e for e in student.history if e.get("course_title") == course.title), None)
                    if entry and "grade" in entry:
                        course_grades.append(entry["grade"])
                        all_grades.append(entry["grade"])

                if course_grades:
                    avg_grade = sum(course_grades) / len(course_grades)
                    completed_courses_data.append({
                        "title": course.title,
                        "avg_grade": round(avg_grade, 2),
                        "num_students": len(course_grades)
                    })

        # Вычисляем общую среднюю успеваемость по всем курсам
        avg_success_rate = round(sum(all_grades) / len(all_grades), 2) if all_grades else None

        return {
            "teacher": teacher,
            "num_active_courses": num_active_courses,
            "avg_success_rate": avg_success_rate,
            "completed_courses": completed_courses_data
        }

    def save_to_json(self):
        """Сохраняет текущее состояние в JSON."""
        data = {
            "students": [{"id": s.id, "name": s.name, "email": s.email, "history": s.history} for s in self.students],
            "teachers": [{"id": t.id, "name": t.name, "specialization": t.specialization} for t in self.teachers],
            "courses": [{
                "id": c.id,
                "title": c.title,
                "topic": c.topic,
                "status": c.status,
                "students": c.students,
                "teacher_id": c.teacher_id,
                "modules": c.modules
            } for c in self.courses],
            "modules": [{
                "id": m.id,
                "title": m.title,
                "course_id": m.course_id,
                "lessons": m.lessons
            } for m in self.modules],
            "lessons": [{
                "id": l.id,
                "title": l.title,
                "module_id": l.module_id
            } for l in self.lessons],
            "homeworks": [{
                "id": hw.id,
                "lesson_id": hw.lesson_id,
                "description": hw.description,
                "due_date": hw.due_date
            } for hw in self.homeworks],
            "homework_grades": [{
                "id": hg.id,
                "student_id": hg.student_id,
                "homework_id": hg.homework_id,
                "grade": hg.grade
            } for hg in self.homework_grades],
            "next_ids": self.next_ids
        }

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_from_json(self):
        """Загружает данные из JSON при старте приложения."""
        if not os.path.exists("data.json"):
            return

        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

            for s_data in data.get("students", []):
                student = Student(s_data["id"], s_data["name"], s_data["email"])
                student.history = s_data.get("history", [])
                self.students.append(student)

            for t_data in data.get("teachers", []):
                teacher = Teacher(t_data["id"], t_data["name"], t_data["specialization"])
                self.teachers.append(teacher)

            for c_data in data.get("courses", []):
                course = Course(c_data["id"], c_data["title"], c_data["topic"])
                course.status = c_data.get("status", "активен")
                course.students = c_data.get("students", [])
                course.teacher_id = c_data.get("teacher_id")
                course.modules = c_data.get("modules", [])
                self.courses.append(course)

            for m_data in data.get("modules", []):
                module = Module(m_data["id"], m_data["title"], m_data["course_id"])
                module.lessons = m_data.get("lessons", [])
                self.modules.append(module)

            for l_data in data.get("lessons", []):
                lesson = Lesson(l_data["id"], l_data["title"], l_data["module_id"])
                self.lessons.append(lesson)

            for hw_data in data.get("homeworks", []):
                homework = Homework(
                    hw_data["id"],
                    hw_data["lesson_id"],
                    hw_data["description"],
                    hw_data["due_date"]
                )
                self.homeworks.append(homework)

            for hg_data in data.get("homework_grades", []):
                grade = HomeworkGrade(
                    hg_data["id"],
                    hg_data["student_id"],
                    hg_data["homework_id"],
                    hg_data["grade"]
                )
                self.homework_grades.append(grade)

                # --- Загрузка счетчиков ---
                loaded_next_ids = data.get("next_ids")
                if loaded_next_ids:
                    self.next_ids.update(loaded_next_ids)

        # --- НОВЫЕ МЕТОДЫ: ЭКСПОРТ В CSV ---
    def export_student_report_to_csv(self, student_id):
        """
        Генерирует CSV-отчет по успеваемости студента.
        Возвращает строку с CSV-данными.
        """
        student = self.find_student_by_id(student_id)
        if not student:
            return None


        si = io.StringIO()
        fieldnames = ["Курс", "Оценка", "Преподаватель"]
        writer = csv.DictWriter(si, fieldnames=fieldnames)
        writer.writeheader()

        for entry in student.history:
            course = self.find_course_by_title(entry.get("course_title"))
            teacher_name = "Неизвестно"
            if course and course.teacher_id:
                teacher = self.find_teacher_by_id(course.teacher_id)
                teacher_name = teacher.name if teacher else "Неизвестно"

            writer.writerow({
                "Курс": entry.get("course_title", ""),
                "Оценка": entry.get("grade", ""),
                "Преподаватель": teacher_name
            })

        return si.getvalue()

    def export_teacher_analytics_to_csv(self, teacher_id):
        """
        Генерирует CSV-отчет по аналитике преподавателя.
        Возвращает строку с CSV-данными.
        """
        analytics = self.get_teacher_analytics(teacher_id)
        if not analytics:
            return None

        si = io.StringIO()
        fieldnames = ["Курс", "Средняя оценка", "Количество студентов"]
        writer = csv.DictWriter(si, fieldnames=fieldnames)
        writer.writeheader()

        for course in analytics.get("completed_courses", []):
            writer.writerow({
                "Курс": course["title"],
                "Средняя оценка": course["avg_grade"],
                "Количество студентов": course["num_students"]
            })

        return si.getvalue()
