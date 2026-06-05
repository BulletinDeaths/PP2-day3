class Homework:
    def __init__(self, hw_id: int, lesson_id: int, description: str, due_date: str):
        """
        :param hw_id: Уникальный ID задания
        :param lesson_id: ID урока, к которому привязано задание
        :param description: Текст задания
        :param due_date: Срок сдачи (строка в формате ГГГГ-ММ-ДД)
        """
        self.id = hw_id
        self.lesson_id = lesson_id
        self.description = description
        self.due_date = due_date


class HomeworkGrade:
    """
    Оценка за конкретное домашнее задание конкретного студента.
    """
    def __init__(self, student_id: int, homework_id: int, grade: int):
        """
        :param student_id: ID студента
        :param homework_id: ID домашнего задания
        :param grade: Оценка (от 2 до 5)
        """
        self.student_id = student_id
        self.homework_id = homework_id
        self.grade = grade
