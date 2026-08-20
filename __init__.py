#Anki timer add-on
#vibecoded by Gnandeep Chintala and Gemini

from aqt import mw, gui_hooks
from aqt.qt import QTimer, QLabel, Qt, QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QAction, qconnect, QDialog, QSlider

# Global variables
timer_label = None
study_timer = None
pause_btn = None
container = None
time_left = 0
is_paused = False
current_deck_id = None

# Target times in seconds
sec_per_new = 11      
sec_per_learn = 9     
sec_per_review = 9
settings_dialog = None

def get_dynamic_timer_duration():
    """Calculates total seconds based on remaining cards in the active deck."""
    global sec_per_new, sec_per_learn, sec_per_review
    counts = mw.col.sched.counts()
    if not counts:
        return 0 
        
    new_cards, learning_cards, review_cards = counts   
    
    return (new_cards * sec_per_new) + (learning_cards * sec_per_learn) + (review_cards * sec_per_review)

def update_display():
    global time_left
    mins, secs = divmod(time_left, 60)
    timer_label.setText(f"{mins:02d}:{secs:02d}")
    # Made the font slightly larger so it fills the new square shape nicely
    timer_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background: transparent;")

def update_timer():
    global time_left
    if time_left > 0:
        time_left -= 1
        update_display()
    else:
        timer_label.setText("Time's up!")
        timer_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #FF2800; background: transparent;")
        study_timer.stop()

def toggle_timer():
    global is_paused
    if is_paused:
        study_timer.start(1000)
        pause_btn.setText("Pause")
        is_paused = False
    else:
        study_timer.stop()
        pause_btn.setText("Resume")
        is_paused = True

def reset_timer():
    global time_left

    new_duration = get_dynamic_timer_duration()
    time_left = new_duration if new_duration > 0 else 0

    update_display()
    if is_paused:
        toggle_timer()

def add_time():
    global time_left
    time_left += 5 * 60
    update_display()

def remove_time():
    global time_left
    time_left = max(0, time_left - 5 * 60) 
    update_display()

# 1. THE TOGGLE FUNCTION
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
        
        layout = QVBoxLayout()
        
        # New Cards Slider
        self.new_label = QLabel(f"New Cards: {sec_per_new}s")
        self.new_slider = QSlider(Qt.Orientation.Horizontal)
        self.new_slider.setRange(1, 20)
        self.new_slider.setValue(sec_per_new)
        self.new_slider.valueChanged.connect(self.update_new)
        
        # Learn Cards Slider
        self.learn_label = QLabel(f"Learn Cards: {sec_per_learn}s")
        self.learn_slider = QSlider(Qt.Orientation.Horizontal)
        self.learn_slider.setRange(1, 20)
        self.learn_slider.setValue(sec_per_learn)
        self.learn_slider.valueChanged.connect(self.update_learn)
        
        # Review Cards Slider
        self.review_label = QLabel(f"Review Cards: {sec_per_review}s")
        self.review_slider = QSlider(Qt.Orientation.Horizontal)
        self.review_slider.setRange(1, 20)
        self.review_slider.setValue(sec_per_review)
        self.review_slider.valueChanged.connect(self.update_review)
        
        # Move the toggle visibility button into this menu
        self.toggle_btn = QPushButton("Show/Hide Timer on Screen")
        self.toggle_btn.clicked.connect(toggle_timer_visibility)
        
        # Add widgets to layout
        layout.addWidget(self.new_label)
        layout.addWidget(self.new_slider)
        layout.addWidget(self.learn_label)
        layout.addWidget(self.learn_slider)
        layout.addWidget(self.review_label)
        layout.addWidget(self.review_slider)
        layout.addSpacing(10)
        layout.addWidget(self.toggle_btn)
        
        self.setLayout(layout)
        
    def update_new(self, val):
        global sec_per_new
        sec_per_new = val
        self.new_label.setText(f"New Cards: {val}s")
        reset_timer() # Recalculates immediately
        
    def update_learn(self, val):
        global sec_per_learn
        sec_per_learn = val
        self.learn_label.setText(f"Learn Cards: {val}s")
        reset_timer()
        
    def update_review(self, val):
        global sec_per_review
        sec_per_review = val
        self.review_label.setText(f"Review Cards: {val}s")
        reset_timer()

def open_settings_dialog():
    global settings_dialog
    if not settings_dialog:
        settings_dialog = TimerSettingsDialog(mw)
    settings_dialog.show()
    settings_dialog.raise_()
    settings_dialog.activateWindow()

# --- CHANGED: Renamed the Tools menu item and pointed it to the new settings dialog ---
action = QAction("Anki Timer", mw)
qconnect(action.triggered, open_settings_dialog)
mw.form.menuTools.addAction(action)

# Add the toggle button directly to Anki's Tools menu
#action = QAction("Anki Timer", mw)
#qconnect(action.triggered, toggle_timer_visibility)
#mw.form.menuTools.addAction(action)

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
        
        # 2. NEW SHAPE: 180 pixels wide, 90 pixels tall (more square)
        container.setGeometry(x_position, y_position, 180, 90) 
        
        # 3. MORE TRANSLUCENT: Dropped the opacity from 180 to 80
        container.setStyleSheet("background-color: rgba(0, 0, 0, 80); border-radius: 10px;")
        
        # 4. NEW LAYOUT: Stack the timer on top of the buttons
        main_layout = QVBoxLayout()
        
        timer_label = QLabel()
        update_display()
        timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create a sub-layout just for the buttons to sit side-by-side
        btn_layout = QHBoxLayout()
        
        minus_btn = QPushButton("-")
        # Made the buttons slightly translucent too so they blend in
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
        
        # Add everything together
        btn_layout.addWidget(minus_btn)
        btn_layout.addWidget(plus_btn)
        btn_layout.addWidget(pause_btn)
        btn_layout.addWidget(reset_btn)
        
        main_layout.addWidget(timer_label)
        main_layout.addLayout(btn_layout)
        
        container.setLayout(main_layout)
        
        # 5. Hide it by default so you have to toggle it on
        container.hide()

    if not study_timer:
        study_timer = QTimer(mw)
        study_timer.timeout.connect(update_timer)
    
    study_timer.start(1000)

# 1. THE AUTOMATION FUNCTION
def auto_show_timer(next_state: str, old_state: str):
    """Automatically shows the timer in decks and hides it on the home screen."""
    global container, time_left, current_deck_id
    if container:
        # Show the timer on the deck overview or review screens
        if next_state in ["overview", "review"]:
            # Using .get('id') safely pulls the ID of the active deck
            active_deck_id = mw.col.decks.current().get('id')

            # This prevents the timer from resetting if you just click between review and overview
            #triggers if you enter a new deck or com from deck browser
            if active_deck_id != current_deck_id or old_state == "deckBrowser":
                current_deck_id = active_deck_id

                #Fetch the new time based on this specific deck's cards
                new_duration = get_dynamic_timer_duration()
                time_left = new_duration  # Will properly set to 0 if the deck is empty
                update_display()

            container.show()
        # Hide the timer when returning to the main deck browser
        elif next_state == "deckBrowser":
            #Clear the deck ID so it's ready to recalculate next time you click a deck ---
            current_deck_id = None 
            container.hide()

gui_hooks.profile_did_open.append(setup_timer_ui)
gui_hooks.state_shortcuts_will_change.append(setup_shortcuts)
# Attach our automation function to Anki's state changes
gui_hooks.state_did_change.append(auto_show_timer)