class Module:
    def __init__(self, module_id: int, title: str, course_id: int):
        self.id = module_id
        self.title = title
        self.course_id = course_id
        self.lessons = []

    def add_lesson(self, lesson_id):
        """Добавляет урок в модуль."""
        if lesson_id not in self.lessons:
            self.lessons.append(lesson_id)
