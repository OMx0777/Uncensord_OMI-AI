import sys
import os
import time
import markdown
import ollama
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextBrowser, QLineEdit, QPushButton, 
                             QFileDialog, QProgressBar, QFrame, QLabel, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QUrl, QPoint, QRect
from PyQt6.QtGui import (QIcon, QFont, QColor, QPalette, QPainter, QLinearGradient, 
                         QRadialGradient, QPen, QBrush, QTextCursor, QTextCharFormat, QDesktopServices)

# --- CUSTOM BROWSER (FIXED MOUSE HANDLING) ---
class ChatBrowser(QTextBrowser):
    copy_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(False) 

    def mouseReleaseEvent(self, event):
        # check if mouse clicked on an anchor (link)
        url_str = self.anchorAt(event.pos())
        
        if url_str:
            # IT IS A LINK
            if url_str.startswith("copy:"):
                # It's our copy button!
                try:
                    index = int(url_str.split(":")[1])
                    self.copy_requested.emit(index)
                except ValueError:
                    pass
                # RETURN HERE to prevent QTextBrowser from trying to navigate
                return 
            
            else:
                # It's a real website link
                QDesktopServices.openUrl(QUrl(url_str))
                # RETURN HERE to prevent internal navigation
                return

        # If it wasn't a link, do normal behavior (text selection, etc.)
        super().mouseReleaseEvent(event)

# --- ARC REACTOR WIDGET ---
class ArcReactorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self.rotation_angle = 0
        self.pulse_scale = 1.0
        self.pulse_direction = 1
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)  # ~33 FPS
        
    def update_animation(self):
        self.rotation_angle = (self.rotation_angle + 2) % 360
        
        # Pulsing effect
        self.pulse_scale += 0.01 * self.pulse_direction
        if self.pulse_scale >= 1.15 or self.pulse_scale <= 0.95:
            self.pulse_direction *= -1
            
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Outer glow
        for i in range(5, 0, -1):
            glow_gradient = QRadialGradient(center_x, center_y, 80 + i * 8)
            glow_gradient.setColorAt(0, QColor(100, 255, 150, 30 - i * 5))
            glow_gradient.setColorAt(1, QColor(0, 255, 100, 0))
            painter.setBrush(QBrush(glow_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center_x - (80 + i * 8), center_y - (80 + i * 8), 
                              (80 + i * 8) * 2, (80 + i * 8) * 2)
        
        # Rotating outer ring
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation_angle)
        
        # Draw triangular segments
        for i in range(12):
            angle = i * 30
            painter.save()
            painter.rotate(angle)
            
            gradient = QLinearGradient(0, -70, 0, -50)
            gradient.setColorAt(0, QColor(0, 255, 100, 200))
            gradient.setColorAt(1, QColor(100, 255, 150, 100))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(150, 255, 200), 1))
            
            # Triangle shape
            points = [QPoint(0, -70), QPoint(-8, -50), QPoint(8, -50)]
            painter.drawPolygon(points)
            painter.restore()
        
        painter.restore()
        
        # Middle ring (counter-rotating)
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(-self.rotation_angle * 1.5)
        
        for i in range(8):
            angle = i * 45
            painter.save()
            painter.rotate(angle)
            
            gradient = QLinearGradient(0, -50, 0, -35)
            gradient.setColorAt(0, QColor(50, 200, 100, 180))
            gradient.setColorAt(1, QColor(100, 255, 150, 80))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(150, 255, 200), 1))
            
            painter.drawRect(-4, -50, 8, 15)
            painter.restore()
        
        painter.restore()
        
        # Core circle with pulsing effect
        scaled_radius = int(35 * self.pulse_scale)
        
        # Core glow
        core_glow = QRadialGradient(center_x, center_y, scaled_radius + 15)
        core_glow.setColorAt(0, QColor(200, 255, 220, 200))
        core_glow.setColorAt(0.5, QColor(100, 255, 150, 150))
        core_glow.setColorAt(1, QColor(0, 255, 100, 0))
        
        painter.setBrush(QBrush(core_glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_x - (scaled_radius + 15), center_y - (scaled_radius + 15),
                          (scaled_radius + 15) * 2, (scaled_radius + 15) * 2)
        
        # Core
        core_gradient = QRadialGradient(center_x, center_y, scaled_radius)
        core_gradient.setColorAt(0, QColor(220, 255, 230))
        core_gradient.setColorAt(0.6, QColor(100, 255, 150))
        core_gradient.setColorAt(1, QColor(0, 255, 100))
        
        painter.setBrush(QBrush(core_gradient))
        painter.setPen(QPen(QColor(150, 255, 200), 2))
        painter.drawEllipse(center_x - scaled_radius, center_y - scaled_radius,
                          scaled_radius * 2, scaled_radius * 2)
        
        # Center bright spot
        center_spot = QRadialGradient(center_x - 8, center_y - 8, 15)
        center_spot.setColorAt(0, QColor(255, 255, 255, 250))
        center_spot.setColorAt(1, QColor(200, 255, 220, 0))
        
        painter.setBrush(QBrush(center_spot))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_x - 15, center_y - 15, 30, 30)

# --- WORKER THREAD (Backend Logic) ---
class OllamaWorker(QThread):
    new_chunk = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, model, messages):
        super().__init__()
        self.model = model
        self.messages = messages

    def run(self):
        try:
            stream = ollama.chat(model=self.model, messages=self.messages, stream=True)
            for chunk in stream:
                content = chunk['message']['content']
                self.new_chunk.emit(content)
        except Exception as e:
            self.new_chunk.emit(f"\n[Error: {str(e)}]")
        finally:
            self.finished.emit()

# --- MAIN WINDOW ---
class OMIWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("OMI - No ethics allowed")
        self.resize(1200, 900)
        
        # Data
        self.messages = []
        self.full_history_text = ""
        self.is_generating = False
        self.current_ai_response = ""
        
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # === HEADER WITH ARC REACTOR ===
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(250)
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Arc Reactor
        self.arc_reactor = ArcReactorWidget()
        header_layout.addWidget(self.arc_reactor, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title_label = QLabel("OMI")
        title_label.setObjectName("Title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("AI with no ethics")
        subtitle_label.setObjectName("Subtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        # Status indicator
        self.status_label = QLabel("● ONLINE")
        self.status_label.setObjectName("Status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.status_label)
        
        self.main_layout.addWidget(header)
        
        # === CIRCUIT LINES DECORATION ===
        circuit_frame = QFrame()
        circuit_frame.setObjectName("CircuitLines")
        circuit_frame.setFixedHeight(3)
        self.main_layout.addWidget(circuit_frame)
        
        # === CHAT AREA ===
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(30, 20, 30, 20)
        
        # USE CUSTOM BROWSER HERE
        self.chat_display = ChatBrowser()
        self.chat_display.copy_requested.connect(self.copy_response)
        self.chat_display.setStyleSheet("line-height: 1.5;")
        chat_layout.addWidget(self.chat_display)
        
        # Typing indicator
        self.typing_indicator = QLabel()
        self.typing_indicator.setObjectName("TypingIndicator")
        self.typing_indicator.hide()
        chat_layout.addWidget(self.typing_indicator)
        
        # Typing animation timer
        self.typing_dots = 0
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.update_typing_indicator)
        
        # Progress Line (Neon Loader)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(3)
        self.progress.setTextVisible(False)
        self.progress.hide()
        chat_layout.addWidget(self.progress)
        
        self.main_layout.addWidget(chat_container)
        
        # === INPUT AREA ===
        input_outer = QFrame()
        input_outer.setObjectName("InputOuter")
        input_outer_layout = QVBoxLayout(input_outer)
        input_outer_layout.setContentsMargins(30, 15, 30, 25)
        
        input_container = QFrame()
        input_container.setObjectName("InputContainer")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(20, 12, 20, 12)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(45, 45)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        input_outer_layout.addWidget(input_container)
        
        # Footer Toolbar
        tool_layout = QHBoxLayout()
        tool_layout.setContentsMargins(0, 10, 0, 0)
        
        self.save_btn = QPushButton("💾 SAVE LOG")
        self.save_btn.setObjectName("TextBtn")
        self.save_btn.clicked.connect(self.save_chat)
        
        self.clear_btn = QPushButton("🗑️ CLEAR MEMORY")
        self.clear_btn.setObjectName("TextBtn")
        self.clear_btn.clicked.connect(self.clear_chat)
        
        tool_layout.addWidget(self.save_btn)
        tool_layout.addStretch()
        tool_layout.addWidget(self.clear_btn)
        
        input_outer_layout.addLayout(tool_layout)
        
        self.main_layout.addWidget(input_outer)
        
        # Apply The Iron Man Theme
        self.apply_styles()

    def apply_styles(self):
        # Dark Green Theme Palette
        bg_dark = "#0a0a0f"
        green_primary = "#00ff00"
        green_glow = "#00ff88"
        green_dark = "#00aa00"
        chat_bg = "#0f0f15"
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0f0a, stop:0.3 #050a05, stop:1 #0a0a0f);
            }}
            
            /* Header */
            QFrame#Header {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1f1a, stop:1 #0a0f0a);
                border-bottom: 2px solid {green_primary};
            }}
            
            QLabel#Title {{
                color: {green_primary};
                font-size: 32px;
                font-weight: bold;
                font-family: 'Arial Black', sans-serif;
                text-transform: uppercase;
                letter-spacing: 4px;
                margin-top: 10px;
            }}
            
            QLabel#Subtitle {{
                color: {green_glow};
                font-size: 11px;
                font-family: 'Courier New', monospace;
                letter-spacing: 2px;
                margin-top: 5px;
                opacity: 0.8;
            }}
            
            QLabel#Status {{
                color: {green_primary};
                font-size: 10px;
                font-family: 'Courier New', monospace;
                margin-top: 5px;
                font-weight: bold;
            }}
            
            /* Circuit decoration */
            QFrame#CircuitLines {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {green_dark}, stop:0.5 {green_primary}, stop:1 {green_dark});
            }}
            
            /* Chat Display */
            QTextBrowser {{
                background-color: {chat_bg};
                border: 2px solid {green_primary};
                border-radius: 10px;
                padding: 15px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 14px;
                color: {green_glow};
                selection-background-color: {green_dark};
                selection-color: black;
            }}
            
            /* Typing Indicator */
            QLabel#TypingIndicator {{
                color: {green_glow};
                font-size: 12px;
                font-family: 'Consolas', monospace;
                padding: 10px 20px;
                opacity: 0.7;
            }}
            
            QScrollBar:vertical {{
                border: none;
                background: #1a1a20;
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {green_primary};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            
            /* Input Container */
            QFrame#InputOuter {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {bg_dark}, stop:1 #0a0f0a);
            }}
            
            QFrame#InputContainer {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1f1a, stop:1 #1a1a20);
                border: 2px solid {green_primary};
                border-radius: 25px;
            }}
            
            QLineEdit {{
                background-color: transparent;
                color: {green_primary};
                border: none;
                font-size: 15px;
                font-family: 'Consolas', monospace;
                padding: 5px;
            }}
            
            QLineEdit::placeholder {{
                color: #444444;
            }}
            
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {green_glow}, stop:1 {green_primary});
                color: #000000;
                border: 2px solid {green_primary};
                border-radius: 22px;
                font-weight: bold;
                font-size: 18px;
            }}
            
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {green_primary}, stop:1 {green_glow});
                border: 2px solid {green_glow};
            }}
            
            QPushButton:pressed {{
                background: {green_primary};
            }}
            
            QPushButton:disabled {{
                background: #333333;
                color: #666666;
                border: 2px solid #555555;
            }}
            
            /* Footer Buttons */
            QPushButton#TextBtn {{
                background-color: transparent;
                color: #666666;
                font-size: 11px;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 8px 15px;
                font-family: 'Arial', sans-serif;
            }}
            
            QPushButton#TextBtn:hover {{
                color: {green_primary};
                border: 1px solid {green_dark};
                background: rgba(0, 255, 0, 0.1);
            }}
            
            /* Loader */
            QProgressBar {{
                background-color: transparent;
                border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {green_dark}, stop:0.5 {green_primary}, stop:1 {green_dark});
                border-radius: 1px;
            }}
        """)

    def format_user_message(self, text):
        html_content = markdown.markdown(text)
        # Right aligned, Dark Green bubble for USER
        return f"""
        <br>
        <div align="right">
            <div style="
                background-color: #0d2b0d; 
                color: #00ff00; 
                border: 1px solid #005500;
                border-radius: 15px; 
                padding: 12px; 
                margin-left: 100px;
                text-align: left;
                font-family: 'Segoe UI', sans-serif;">
                <b style="font-size: 10px; color: #00aa00;">💀 YOU</b><br>
                {html_content}
            </div>
        </div>
        <br>
        """
        
    def format_ai_header(self):
        # Header for AI message (Left aligned)
        return """
        <br>
        <div align="left" style="margin-bottom: 5px;">
            <b style="font-size: 12px; color: #00ff88; font-family: 'Segoe UI', sans-serif;">☠️ OMI:</b>
        </div>
        """

    def get_copy_button_html(self, index):
        # Creates a link that looks like a small button.
        # The href 'copy:{index}' tells our handler which message to copy.
        return f"""
        <br>
        <div align="left">
            <a href="copy:{index}" style="
                text-decoration: none; 
                color: #00ff00; 
                background-color: #0a1a0a;
                border: 1px solid #005500;
                font-family: sans-serif;
                font-size: 10px;
                padding: 4px 10px;
                border-radius: 5px;
            ">📋 COPY RESPONSE</a>
        </div>
        <br>
        """

    # NEW FUNCTION TO HANDLE THE SIGNAL FROM CHAT BROWSER
    def copy_response(self, index):
        try:
            content = self.messages[index]['content']
            QApplication.clipboard().setText(content)
            
            # Feedback
            self.status_label.setText("● COPIED TO CLIPBOARD")
            self.status_label.setStyleSheet("color: #ffffff;")
            QTimer.singleShot(2000, lambda: self.status_label.setText("● ONLINE"))
            QTimer.singleShot(2000, lambda: self.status_label.setStyleSheet("color: #00ff00;"))
        except Exception as e:
            print(f"Copy error: {e}")

    def update_typing_indicator(self):
        self.typing_dots = (self.typing_dots + 1) % 4
        dots = "." * self.typing_dots
        self.typing_indicator.setText(f"☠️ OMI is thinking{dots}   ")
    
    def send_message(self):
        text = self.input_field.text().strip()
        if not text or self.is_generating:
            return

        # 1. Show User Message on the RIGHT
        self.chat_display.append(self.format_user_message(text))
        
        self.messages.append({"role": "user", "content": text})
        self.full_history_text += f"OM: {text}\n\n"
        
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
        
        # Reset Input
        self.input_field.clear()
        self.input_field.setDisabled(True)
        self.send_btn.setDisabled(True)
        self.is_generating = True
        
        self.typing_indicator.show()
        self.typing_timer.start(500)
        self.progress.show()
        self.status_label.setText("● PROCESSING")
        
        self.current_ai_response = ""
        
        self.worker = OllamaWorker("OMI", self.messages)
        self.worker.new_chunk.connect(self.update_ai_response)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.start()

    def update_ai_response(self, chunk):
        if not self.current_ai_response:
            self.typing_indicator.hide()
            self.typing_timer.stop()
            self.chat_display.append(self.format_ai_header())
            
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("#00ff88"))
            fmt.setFontPointSize(12)
            cursor.setCharFormat(fmt)
            self.chat_display.setTextCursor(cursor)
        
        self.current_ai_response += chunk
        self.chat_display.insertPlainText(chunk)
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def on_generation_finished(self):
        # Save the message to history first
        self.messages.append({"role": "assistant", "content": self.current_ai_response})
        self.full_history_text += f"OMI: {self.current_ai_response}\n\n"
        
        # Determine the index of the message we just added
        # It is the last item in the list, so index = len - 1
        msg_index = len(self.messages) - 1
        
        # Append the COPY button
        self.chat_display.append(self.get_copy_button_html(msg_index))
        
        self.typing_indicator.hide()
        self.typing_timer.stop()
        self.input_field.setDisabled(False)
        self.send_btn.setDisabled(False)
        self.input_field.setFocus()
        self.progress.hide()
        self.status_label.setText("● ONLINE")
        self.is_generating = False
        
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def save_chat(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Chat Log", "OMI_log.txt", "Text Files (*.txt)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.full_history_text)

    def clear_chat(self):
        self.messages = []
        self.full_history_text = ""
        self.chat_display.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = OMIWindow()
    window.show()
    sys.exit(app.exec())