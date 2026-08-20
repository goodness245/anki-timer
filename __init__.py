#Anki timer add-on
#vibecoded by Gnandeep Chintala and Gemini

from aqt import mw, gui_hooks
from aqt.qt import QTimer, QLabel, Qt, QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QAction, qconnect

# Global variables
timer_label = None
study_timer = None
pause_btn = None
container = None
time_left = 60 * 60  
is_paused = False

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
        timer_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #55ff55; background: transparent;")
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
    time_left = 60 * 60
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

# Add the toggle button directly to Anki's Tools menu
action = QAction("Toggle Focus Timer", mw)
qconnect(action.triggered, toggle_timer_visibility)
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
        
        minus_btn = QPushButton("-5m")
        # Made the buttons slightly translucent too so they blend in
        minus_btn.setStyleSheet("color: white; background-color: rgba(68, 68, 68, 150); border-radius: 5px; padding: 4px;")
        minus_btn.clicked.connect(remove_time)
        
        plus_btn = QPushButton("+5m")
        plus_btn.setStyleSheet("color: white; background-color: rgba(68, 68, 68, 150); border-radius: 5px; padding: 4px;")
        plus_btn.clicked.connect(add_time)
        
        pause_btn = QPushButton("Pause")
        pause_btn.setStyleSheet("color: white; background-color: rgba(68, 68, 68, 150); border-radius: 5px; padding: 4px;")
        pause_btn.clicked.connect(toggle_timer)
        
        # Add everything together
        btn_layout.addWidget(minus_btn)
        btn_layout.addWidget(plus_btn)
        btn_layout.addWidget(pause_btn)
        
        main_layout.addWidget(timer_label)
        main_layout.addLayout(btn_layout)
        
        container.setLayout(main_layout)
        
        # 5. Hide it by default so you have to toggle it on
        container.hide()

    if not study_timer:
        study_timer = QTimer(mw)
        study_timer.timeout.connect(update_timer)
    
    study_timer.start(1000)

gui_hooks.profile_did_open.append(setup_timer_ui)
gui_hooks.state_shortcuts_will_change.append(setup_shortcuts)