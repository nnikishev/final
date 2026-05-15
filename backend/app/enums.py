from enum import Enum


class SortOrder(Enum):
    DESC = "desc"
    ASC = "asc"

    def __str__(self):
        return self.value
    

class QualityClass(Enum):
    A = "A (Отборное, сучки отсутствуют или очень мелкие, единичные)"
    B = "B — (Хорошее, сучки средние, здоровые, допустимы)"
    C = "C (Среднее - много сучков)"
    D = "D — (Низкое, гниль, выпадающие сучки, трещины, обзол)"