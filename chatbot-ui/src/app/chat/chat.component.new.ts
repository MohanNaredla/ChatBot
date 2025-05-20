import {
  Component,
  OnInit,
  OnDestroy,
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
export class ChatComponent implements OnInit, AfterViewChecked, OnDestroy {
  @Input() expanded = false;
  @Output() expand = new EventEmitter<boolean>();
  @Output() close = new EventEmitter<void>();
  @ViewChild('chatContainer') private chatContainer!: ElementRef;

  userMessage = '';
  messages: Message[] = [];
  loading = false;
  backendUnavailable = false;
  isListening = false;

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
    // Check Rasa backend
    fetch('http://localhost:5005/version')
      .then(() => {
        this.backendUnavailable = false;
        // Also check STT service availability
        return fetch('http://localhost:5006/health')
          .then(response => {
            if (!response.ok) {
              console.warn('STT service returned error status');
            } else {
              console.info('STT service is available');
            }
          })
          .catch(err => console.warn('STT service unavailable:', err));
      })
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

  startRecording(): void {
    if (this.isListening || this.loading) {
      return;
    }
    
    console.log('Starting speech recognition...');
    this.isListening = true;
    this.loading = true;
    
    // Trigger the server-side speech recognition
    fetch('http://localhost:5006/stt', {
      method: 'POST',
      signal: AbortSignal.timeout(10000) // 10 second timeout
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        if (data && data.text) {
          if (data.text.trim()) {
            this.userMessage = data.text;
            
            // Auto-send if confidence is high
            if (data.confidence && data.confidence > 0.8) {
              this.sendMessage();
            }
          } else {
            console.warn('Received empty transcription from STT service');
            this.userMessage = ''; // Clear any previous message
          }
        } else if (data && data.error) {
          console.error('STT service error:', data.error);
          alert('Could not understand audio. Please try again.');
        }
      })
      .catch(error => {
        console.error('Error processing speech:', error);
        if (error.name !== 'AbortError') {
          alert('Error processing speech. Please try again.');
        }
      })
      .finally(() => {
        this.isListening = false;
        this.loading = false;
      });
  }

  stopRecording(): void {
    // Since recording is handled server-side, just update UI state
    if (this.isListening) {
      console.log('Stopping speech recognition indicator');
      this.isListening = false;
    }
  }

  ngOnDestroy(): void {
    // No cleanup needed since we're not using browser's audio API
  }

  formatTimestamp(d: Date): string {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}
