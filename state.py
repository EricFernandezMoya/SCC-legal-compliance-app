# state.py

class AppState:
    def __init__(self):
        self.second_window_open = False
        self.current_user = None  # will hold a User instance after login
        self.selected_document_name = None


state = AppState()
