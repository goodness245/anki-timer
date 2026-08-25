#Anki timer add-on
#vibecoded by Gnandeep Chintala and Gemini

from aqt import mw, gui_hooks
from aqt.qt import QTimer, QLabel, Qt, QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QAction, qconnect, QDialog, QSlider, QRadioButton, QButtonGroup

# Global variables
timer_label = None
study_timer = None
pause_btn = None
container = None
time_left = 0
is_paused = False
current_deck_id = None
settings_dialog = None

# Mode tracking and stopwatch variables
current_mode = "countdown"  # Can be "countdown" or "stopwatch"
stopwatch_time = 0

# Target times in seconds
sec_per_new = 9      
sec_per_learn = 7     
sec_per_review = 7

def get_dynamic_timer_duration():
    """Calculates total seconds based on remaining cards in the active deck."""
    global sec_per_new, sec_per_learn, sec_per_review
    counts = mw.col.sched.counts()
    if not counts:
        return 0 
        
    new_cards, learning_cards, review_cards = counts   
    
    return (new_cards * sec_per_new) + (learning_cards * sec_per_learn) + (review_cards * sec_per_review)

def update_display():
    global time_left, stopwatch_time, current_mode
    
    display_time = time_left if current_mode == "countdown" else stopwatch_time
    
    hours, remainder = divmod(display_time, 3600)
    mins, secs = divmod(remainder, 60)
    
    if hours > 0:
        timer_label.setText(f"{hours}:{mins:02d}:{secs:02d}")
    else:
        timer_label.setText(f"{mins:02d}:{secs:02d}")
        
    timer_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background: transparent;")

def update_timer():
    global time_left, stopwatch_time, current_mode
    if current_mode == "countdown":
        if time_left > 0:
            time_left -= 1
            update_display()
        else:
            timer_label.setText("Time's up!")
            timer_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #FF2800; background: transparent;")
            study_timer.stop()
    elif current_mode == "stopwatch":
        stopwatch_time += 1
        update_display()

def toggle_timer():
    global is_paused
    if is_paused:
        study_timer.start(1000)
        pause_btn.setText("Pause")
        is_paused = False
    else:
        study_timer.stop()
        # Changed this label to "Start" so it reads better for a stopwatch
        pause_btn.setText("Start")
        is_paused = True

def reset_timer():
    global time_left, stopwatch_time, current_mode

    if current_mode == "countdown":
        new_duration = get_dynamic_timer_duration()
        time_left = new_duration if new_duration > 0 else 0
    else:
        stopwatch_time = 0

    update_display()
    if is_paused:
        toggle_timer()

def add_time():
    global time_left, current_mode
    if current_mode == "countdown":
        time_left += 5 * 60
        update_display()

def remove_time():
    global time_left, current_mode
    if current_mode == "countdown":
        time_left = max(0, time_left - 5 * 60) 
        update_display()

def toggle_timer_visibility():
    """Shows or hides the timer container when clicked in the menu."""
    global container
    if container:
        if container.isVisible():
            container.hide()
        else:
            container.show()

class TimerSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anki Timer Settings")
        self.setMinimumWidth(300)
        
        main_layout = QVBoxLayout()

        main_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)

        # --- RADIO BUTTONS FOR MODE SELECTION ---
        self.mode_group = QButtonGroup(self)
        self.radio_countdown = QRadioButton("Countdown Timer (Deck)")
        
        # Updated this label
        self.radio_stopwatch = QRadioButton("Stopwatch (Overall Session)")
        
        self.mode_group.addButton(self.radio_countdown)
        self.mode_group.addButton(self.radio_stopwatch)
        
        self.radio_countdown.toggled.connect(self.update_mode)
        
        main_layout.addWidget(QLabel("<b>Timer Mode:</b>"))
        main_layout.addWidget(self.radio_countdown)
        main_layout.addWidget(self.radio_stopwatch)
        main_layout.addSpacing(10)
        
        # --- SLIDER CONTAINER (Hideable) ---
        self.slider_widget = QWidget()
        slider_layout = QVBoxLayout()
        slider_layout.setContentsMargins(0, 0, 0, 0)
        
        slider_layout.addWidget(QLabel("<b>Countdown Target Times:</b>"))
        
        self.new_label = QLabel(f"New Cards: {sec_per_new}s")
        self.new_slider = QSlider(Qt.Orientation.Horizontal)
        self.new_slider.setRange(1, 20)
        self.new_slider.setValue(sec_per_new)
        self.new_slider.valueChanged.connect(self.update_new)
        
        self.learn_label = QLabel(f"Learn Cards: {sec_per_learn}s")
        self.learn_slider = QSlider(Qt.Orientation.Horizontal)
        self.learn_slider.setRange(1, 20)
        self.learn_slider.setValue(sec_per_learn)
        self.learn_slider.valueChanged.connect(self.update_learn)
        
        self.review_label = QLabel(f"Review Cards: {sec_per_review}s")
        self.review_slider = QSlider(Qt.Orientation.Horizontal)
        self.review_slider.setRange(1, 20)
        self.review_slider.setValue(sec_per_review)
        self.review_slider.valueChanged.connect(self.update_review)
        
        slider_layout.addWidget(self.new_label)
        slider_layout.addWidget(self.new_slider)
        slider_layout.addWidget(self.learn_label)
        slider_layout.addWidget(self.learn_slider)
        slider_layout.addWidget(self.review_label)
        slider_layout.addWidget(self.review_slider)
        
        self.slider_widget.setLayout(slider_layout)
        main_layout.addWidget(self.slider_widget)
        
        main_layout.addSpacing(10)
        
        # --- TOGGLE VISIBILITY BUTTON ---
        self.toggle_btn = QPushButton("Show/Hide Timer on Screen")
        self.toggle_btn.clicked.connect(toggle_timer_visibility)
        main_layout.addWidget(self.toggle_btn)
        
        self.setLayout(main_layout)
        
        # Set initial state
        if current_mode == "countdown":
            self.radio_countdown.setChecked(True)
            self.slider_widget.show()
        else:
            self.radio_stopwatch.setChecked(True)
            self.slider_widget.hide()

    def update_mode(self):
        """Toggles the mode and hides/shows the sliders."""
        global current_mode
        if self.radio_countdown.isChecked():
            current_mode = "countdown"
            self.slider_widget.show()
        else:
            current_mode = "stopwatch"
            self.slider_widget.hide()

        self.adjustSize()
        reset_timer()
        
    def update_new(self, val):
        global sec_per_new
        sec_per_new = val
        self.new_label.setText(f"New Cards: {val}s")
        if current_mode == "countdown": reset_timer()
        
    def update_learn(self, val):
        global sec_per_learn
        sec_per_learn = val
        self.learn_label.setText(f"Learn Cards: {val}s")
        if current_mode == "countdown": reset_timer()
        
    def update_review(self, val):
        global sec_per_review
        sec_per_review = val
        self.review_label.setText(f"Review Cards: {val}s")
        if current_mode == "countdown": reset_timer()

def open_settings_dialog():
    global settings_dialog
    if not settings_dialog:
        settings_dialog = TimerSettingsDialog(mw)
    settings_dialog.show()
    settings_dialog.raise_()
    settings_dialog.activateWindow()

action = QAction("Anki Timer", mw)
qconnect(action.triggered, open_settings_dialog)
mw.form.menuTools.addAction(action)

def setup_shortcuts(state: str, shortcuts: list):
    shortcuts.append(("Ctrl+T", toggle_timer))
    shortcuts.append(("Ctrl+R", reset_timer))
    shortcuts.append(("Ctrl+=", add_time))
    shortcuts.append(("Ctrl+-", remove_time))

def setup_timer_ui():
    global timer_label, study_timer, pause_btn, container
    
    if not container:
        container = QWidget(mw)
        
        window_height = mw.height()
        x_position = 20 
        y_position = int(window_height * 0.66) 
        
        container.setGeometry(x_position, y_position, 180, 90) 
        container.setStyleSheet("background-color: rgba(0, 0, 0, 80); border-radius: 10px;")
        
        main_layout = QVBoxLayout()
        
        timer_label = QLabel()
        update_display()
        timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_layout = QHBoxLayout()
        
        minus_btn = QPushButton("-")
        minus_btn.setStyleSheet("color: white; background-color: rgba(68, 68, 68, 150); border-radius: 5px; padding: 4px;")
        minus_btn.clicked.connect(remove_time)
        
        plus_btn = QPushButton("+")
        plus_btn.setStyleSheet("color: white; background-color: rgba(68, 68, 68, 150); border-radius: 5px; padding: 4px;")
        plus_btn.clicked.connect(add_time)
        
        pause_btn = QPushButton("Pause")
        pause_btn.setStyleSheet("color: white; background-color: rgba(68, 68, 68, 150); border-radius: 5px; padding: 4px;")
        pause_btn.clicked.connect(toggle_timer)

        reset_btn = QPushButton("Reset")
        reset_btn.setStyleSheet("color: white; background-color: rgba(68, 68, 68, 150); border-radius: 5px; padding: 4px;")
        reset_btn.clicked.connect(reset_timer)
        
        btn_layout.addWidget(minus_btn)
        btn_layout.addWidget(plus_btn)
        btn_layout.addWidget(pause_btn)
        btn_layout.addWidget(reset_btn)
        
        main_layout.addWidget(timer_label)
        main_layout.addLayout(btn_layout)
        
        container.setLayout(main_layout)
        container.hide()

    if not study_timer:
        study_timer = QTimer(mw)
        study_timer.timeout.connect(update_timer)
    
    study_timer.start(1000)

def auto_show_timer(next_state: str, old_state: str):
    """Automatically shows the timer in decks and hides it on the home screen."""
    global container, time_left, current_deck_id, current_mode
    if container:
        if next_state in ["overview", "review"]:
            active_deck_id = mw.col.decks.current().get('id')

            if active_deck_id != current_deck_id or old_state == "deckBrowser":
                current_deck_id = active_deck_id

                if current_mode == "countdown":
                    new_duration = get_dynamic_timer_duration()
                    time_left = new_duration
                
                update_display()

            container.show()
        elif next_state == "deckBrowser":
            current_deck_id = None 
            container.hide()

gui_hooks.profile_did_open.append(setup_timer_ui)
gui_hooks.state_shortcuts_will_change.append(setup_shortcuts)
gui_hooks.state_did_change.append(auto_show_timer)

# --- CHANGED: Removed the gui_hooks.reviewer_did_show_question line that was resetting the clock! ---