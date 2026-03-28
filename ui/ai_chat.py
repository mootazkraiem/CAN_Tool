from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from typing import List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.anomaly import Anomaly
from core.decoder import DecodedSignal
from core.session_data import SessionDataManager


@dataclass
class ChatMessage:
    role: str
    text: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ChatConversation:
    title: str
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class ChatBubble(QFrame):
    def __init__(self, message: ChatMessage, parent=None):
        super().__init__(parent)
        is_user = message.role == "user"
        self.setObjectName("ChatBubbleUser" if is_user else "ChatBubbleAI")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        bubble = QFrame()
        bubble.setObjectName("ChatBubbleUser" if is_user else "ChatBubbleAI")
        bubble.setMaximumWidth(520)
        bubble.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(14, 10, 14, 10)
        bubble_layout.setSpacing(4)

        text = QLabel(message.text)
        text.setWordWrap(True)
        time_lbl = QLabel(message.timestamp.strftime("%H:%M"))
        time_lbl.setObjectName("MutedLabel")
        bubble_layout.addWidget(text)
        bubble_layout.addWidget(time_lbl, 0, Qt.AlignRight if is_user else Qt.AlignLeft)

        if is_user:
            outer.addStretch()
            outer.addWidget(bubble)
        else:
            outer.addWidget(bubble)
            outer.addStretch()


class AIChatWidget(QWidget):
    QUICK_PROMPTS = [
        "Why is inverter temperature increasing?",
        "Explain anomaly 0x1A2",
        "Summarize the last 5 minutes",
        "What signals are most abnormal?",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session_data: Optional[SessionDataManager] = None
        self._selected_anomaly: Optional[Anomaly] = None
        self._conversations: List[ChatConversation] = []
        self._current_index = -1
        self._build_ui()
        self._start_new_chat("New stream chat")

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        self.splitter = QSplitter(Qt.Horizontal)
        root.addWidget(self.splitter)

        left = QFrame()
        left.setObjectName("SurfaceCard")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        history_head = QHBoxLayout()
        title = QLabel("CHAT HISTORY")
        title.setObjectName("SectionTitle")
        self.new_chat_btn = QPushButton("New Chat")
        self.new_chat_btn.setObjectName("GhostButton")
        self.new_chat_btn.clicked.connect(lambda: self._start_new_chat("Session summary"))
        history_head.addWidget(title)
        history_head.addStretch()
        history_head.addWidget(self.new_chat_btn)

        self.conversation_list = QListWidget()
        self.conversation_list.itemClicked.connect(self._switch_conversation)

        prompt_head = QLabel("QUICK PROMPTS")
        prompt_head.setObjectName("SectionTitle")
        self.prompts = QListWidget()
        for prompt in self.QUICK_PROMPTS:
            self.prompts.addItem(prompt)
        self.prompts.itemClicked.connect(self._apply_prompt)

        self.clear_btn = QPushButton("Clear Selected")
        self.clear_btn.setObjectName("GhostButton")
        self.clear_btn.clicked.connect(self._clear_current_conversation)

        left_layout.addLayout(history_head)
        left_layout.addWidget(self.conversation_list, 2)
        left_layout.addWidget(prompt_head)
        left_layout.addWidget(self.prompts, 1)
        left_layout.addWidget(self.clear_btn)

        right = QFrame()
        right.setObjectName("SurfaceCard")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        chat_title = QLabel("AI CHAT")
        chat_title.setObjectName("SectionTitle")
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.NoFrame)
        self.chat_body = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_body)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch()
        self.chat_scroll.setWidget(self.chat_body)

        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask about the current CAN stream, anomalies, or telemetry...")
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("PrimaryButton")
        self.send_btn.clicked.connect(self._send_prompt)
        self.input.returnPressed.connect(self._send_prompt)
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.send_btn)

        right_layout.addWidget(chat_title)
        right_layout.addWidget(self.chat_scroll, 1)
        right_layout.addLayout(input_row)

        self.splitter.addWidget(left)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([290, 780])

    def set_session_data(self, session_data: SessionDataManager):
        self._session_data = session_data

    def open_analyze_prompt(self, anomaly: Anomaly):
        self._selected_anomaly = anomaly
        self._start_new_chat(f"Analyze anomaly 0x{anomaly.related_can_id:X}")
        self.input.setText(f"Analyze anomaly {anomaly.title} on CAN ID 0x{anomaly.related_can_id:X}")
        self._send_prompt()

    def _start_new_chat(self, title: str):
        conversation = ChatConversation(title=title)
        self._conversations.insert(0, conversation)
        self._current_index = 0
        self._refresh_conversation_list()
        self._render_messages()

    def _refresh_conversation_list(self):
        self.conversation_list.clear()
        for conv in self._conversations:
            item = QListWidgetItem(f"{conv.title}\n{conv.created_at.strftime('%H:%M')}")
            self.conversation_list.addItem(item)
        if self._conversations:
            self.conversation_list.setCurrentRow(self._current_index)

    def _current_conversation(self) -> Optional[ChatConversation]:
        if 0 <= self._current_index < len(self._conversations):
            return self._conversations[self._current_index]
        return None

    def _switch_conversation(self, item: QListWidgetItem):
        self._current_index = self.conversation_list.row(item)
        self._render_messages()

    def _clear_current_conversation(self):
        if not self._conversations:
            return
        self._conversations.pop(self._current_index)
        if not self._conversations:
            self._start_new_chat("New stream chat")
            return
        self._current_index = min(self._current_index, len(self._conversations) - 1)
        self._refresh_conversation_list()
        self._render_messages()

    def _apply_prompt(self, item: QListWidgetItem):
        self.input.setText(item.text())
        self._send_prompt()

    def _send_prompt(self):
        prompt = self.input.text().strip()
        if not prompt:
            return
        conversation = self._current_conversation()
        if conversation is None:
            self._start_new_chat(prompt[:24])
            conversation = self._current_conversation()
        if conversation is None:
            return
        if len(conversation.messages) == 0:
            conversation.title = self._title_for_prompt(prompt)
            self._refresh_conversation_list()
        conversation.messages.append(ChatMessage("user", prompt))
        conversation.messages.append(ChatMessage("assistant", self._respond(prompt)))
        self.input.clear()
        self._render_messages()

    def _render_messages(self):
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        conversation = self._current_conversation()
        if conversation is None or not conversation.messages:
            empty = QLabel("No messages yet. Ask about the active stream or choose a quick prompt.")
            empty.setObjectName("MutedLabel")
            self.chat_layout.addWidget(empty)
            self.chat_layout.addStretch()
        else:
            for message in conversation.messages:
                self.chat_layout.addWidget(ChatBubble(message))
            self.chat_layout.addStretch()
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() < 980:
            self.splitter.setSizes([0, self.width()])
        elif self.splitter.sizes()[0] == 0:
            self.splitter.setSizes([290, max(500, self.width() - 290)])

    def _title_for_prompt(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "anomaly" in lowered:
            return "Analyze anomaly 0x1A2" if "0x1a2" in lowered else "Analyze anomaly"
        if "temperature" in lowered:
            return "Why inverter temp increased"
        if "summarize" in lowered:
            return "Session summary"
        return prompt[:28]

    def _respond(self, prompt: str) -> str:
        if not self._session_data:
            return "Session context is not available yet."

        latest = self._session_data.get_latest_values()
        anomalies = self._session_data.get_active_anomalies()
        all_signals = self._session_data.get_all_signals()

        if self._selected_anomaly and "anomaly" in prompt.lower():
            gap_ms = 0
            related_history = [sig for sig in all_signals if sig.can_id == self._selected_anomaly.related_can_id]
            if len(related_history) >= 2:
                gap_ms = (related_history[-1].timestamp - related_history[-2].timestamp) * 1000.0
            return (
                f"{self._selected_anomaly.title} is active on CAN ID 0x{self._selected_anomaly.related_can_id:X}. "
                f"The current confidence is {self._selected_anomaly.confidence * 100:.1f}% and the latest gap is {gap_ms:.0f} ms. "
                f"Most likely causes are decoder mismatch, a disconnected sender, or bus saturation. "
                f"The active description is: {self._selected_anomaly.description}"
            )

        if "most abnormal" in prompt.lower():
            if not anomalies:
                return "No active anomalies are currently flagged in this stream."
            top = anomalies[:4]
            return "Most abnormal signals right now are " + ", ".join(
                f"{anomaly.title} on 0x{anomaly.related_can_id:X} ({anomaly.confidence * 100:.1f}%)" for anomaly in top
            ) + "."

        if "summarize" in prompt.lower():
            latest_values = ", ".join(
                f"{sig.signal_name}={sig.value:.1f}{sig.unit}" for sig in list(latest.values())[:5]
            )
            return (
                f"This stream contains {len(all_signals)} decoded frames across {len(latest)} active signals. "
                f"There are {len(anomalies)} active anomalies right now. "
                f"Latest values: {latest_values or 'no current signal values'}."
            )

        if "temperature" in prompt.lower():
            temp = latest.get("Inverter Temperature") or latest.get("Motor Temperature")
            if temp:
                history = self._session_data.get_signal_history(temp.signal_name)[-8:]
                trend = "rising" if len(history) >= 2 and history[-1].value > history[0].value else "stable"
                return (
                    f"{temp.signal_name} is {temp.value:.1f} {temp.unit} and currently {trend}. "
                    f"Recent readings average {mean(item.value for item in history):.1f} {temp.unit}. "
                    f"Severity is {temp.severity.upper()}."
                )

        if "0x1a2" in prompt.lower():
            signal = latest.get("Battery Voltage")
            if signal:
                return (
                    f"CAN ID 0x1A2 maps to {signal.signal_name}. "
                    f"It is currently {signal.value:.1f} {signal.unit} with severity {signal.severity.upper()}. "
                    f"Recent history shows {len(self._session_data.get_signal_history(signal.signal_name))} stored samples this session."
                )

        if latest:
            highest = sorted(latest.values(), key=lambda item: (item.severity != "critical", -abs(item.value)))[:3]
            focus = ", ".join(f"{sig.signal_name} {sig.value:.1f}{sig.unit}" for sig in highest)
            return (
                f"The current stream context points to {len(latest)} active signals and {len(anomalies)} active anomalies. "
                f"The strongest live signals right now are {focus}. "
                f"Ask about a specific CAN ID, anomaly, or trend and I can break down likely causes."
            )

        return "I don't have active telemetry yet. Start a stream or load playback data and ask again."
