import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../services/chat.service';
import { Message } from '../models/chat.model';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent implements OnInit, AfterViewChecked {
  userMessage = '';
  messages: Message[] = [];
  loading = false;
  backendUnavailable = false;
  @ViewChild('chatContainer') private chatContainer!: ElementRef;

  constructor(private chatService: ChatService) { }
  ngOnInit(): void {
    this.messages = this.chatService.getMessages();
    // Add a welcome message if there are no messages
    if (this.messages.length === 0) {
      this.chatService.addMessage({
        content: 'Hello! How can I assist you today?',
        sender: 'bot',
        timestamp: new Date()
      });
      this.messages = this.chatService.getMessages();
    }
    
    // Check if backend is available
    this.checkBackendAvailability();
  }
  
  checkBackendAvailability(): void {
    fetch('http://127.0.0.1:8000/chat', { method: 'OPTIONS' })
      .then(() => {
        this.backendUnavailable = false;
      })
      .catch(() => {
        this.backendUnavailable = true;
      });
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  scrollToBottom(): void {
    try {
      this.chatContainer.nativeElement.scrollTop = this.chatContainer.nativeElement.scrollHeight;
    } catch (err) { }
  }
  sendMessage(): void {
    if (!this.userMessage.trim() || this.loading) {
      return;
    }

    const message = this.userMessage.trim();
    this.userMessage = '';
    this.loading = true;

    // Call the service to send the message
    this.chatService.sendMessage(message).subscribe({
      next: (response) => {
        // Add bot response to the messages array
        this.chatService.addMessage({
          content: response.answer,
          sender: 'bot',
          timestamp: new Date()
        });
        this.messages = this.chatService.getMessages();
        this.loading = false;
      },      error: (error) => {
        console.error('Error sending message', error);
        // Add error message
        this.chatService.addMessage({
          content: 'Sorry, there was an error connecting to the service. Please check if the backend server is running correctly.',
          sender: 'bot',
          timestamp: new Date()
        });
        this.messages = this.chatService.getMessages();
        this.loading = false;
        this.backendUnavailable = true;
      }
    });
  }

  clearChat(): void {
    this.chatService.clearMessages();
    this.messages = [];
    // Add back the welcome message
    this.chatService.addMessage({
      content: 'Hello! How can I assist you today?',
      sender: 'bot',
      timestamp: new Date()
    });
    this.messages = this.chatService.getMessages();
  }

  formatTimestamp(date: Date): string {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}
