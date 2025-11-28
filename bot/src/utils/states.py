from aiogram.fsm.state import State, StatesGroup

class AdminAddState(StatesGroup):
    INPUT = State()
    STATUS = State()

class CategoryAddState(StatesGroup):
    NAME=State()
    PHOTO=State()

class ProductAddState(StatesGroup):
    TITLE=State()
    DESCRIPTION=State()
    PRICE=State()
    PHOTO=State()

class CategoryEditState(StatesGroup):
    EDIT=State()

class ProductEditState(StatesGroup):
    EDIT=State()

class PushState(StatesGroup):
    INPUT=State()