from aiogram.fsm.state import State, StatesGroup


class NewIncident(StatesGroup):
    title = State()
    description = State()
    category = State()
    severity = State()


class AddNote(StatesGroup):
    waiting_note = State()


class DetectionScan(StatesGroup):
    waiting_logs = State()
