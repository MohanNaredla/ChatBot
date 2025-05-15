import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  AfterViewChecked,
  Output,
  EventEmitter,
  Input,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../services/chat.service';
import { Message } from '../models/chat.model';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss',
})
export class ChatComponent implements OnInit, AfterViewChecked {
  @Input() expanded = false;
  @Output() expand = new EventEmitter<boolean>();
  @Output() close = new EventEmitter<void>();
  @ViewChild('chatContainer') private chatContainer!: ElementRef;

  userMessage = '';
  messages: Message[] = [];
  loading = false;
  backendUnavailable = false;

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.messages = this.chatService.getMessages();
    if (this.messages.length === 0) {
      this.chatService.addMessage({
        content: 'Hello! How can I assist you today?',
        sender: 'bot',
        timestamp: new Date(),
      });
      this.messages = this.chatService.getMessages();
    }
    this.checkBackendAvailability();
  }

  checkBackendAvailability(): void {
    fetch('http://localhost:5005/version')
      .then(() => (this.backendUnavailable = false))
      .catch(() => (this.backendUnavailable = true));
  }

  ngAfterViewChecked(): void {
    try {
      this.chatContainer.nativeElement.scrollTop =
        this.chatContainer.nativeElement.scrollHeight;
    } catch (_) {}
  }

  sendMessage(): void {
    if (!this.userMessage.trim() || this.loading) return;
    const text = this.userMessage.trim();
    this.userMessage = '';
    this.loading = true;
    this.chatService.sendMessage(text).subscribe({
      next: () => {
        this.messages = this.chatService.getMessages();
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.backendUnavailable = true;
      },
    });
  }

  closeChat(): void {
    this.close.emit();
  }

  toggleExpand(): void {
    this.expand.emit(!this.expanded);
  }

  formatTimestamp(d: Date): string {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}
