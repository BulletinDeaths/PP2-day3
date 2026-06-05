class Course:
    def __init__(self, course_id: int, title: str, topic: str):
        self.id = course_id
        self.title = title
        self.topic = topic
        self.status = "активен"
        self.students = []
        self.teacher_id = None

        self.modules = []

    def add_module(self, module_id):
        """Добавляет модуль в курс."""
        if module_id not in self.modules:
            self.modules.append(module_id)
