import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatComponent } from './chat.component';

@Component({
  selector: 'app-chat-wrapper',
  standalone: true,
  imports: [CommonModule, ChatComponent],
  template: `
    <div class="chat-container-wrapper">
      <!-- Chat Widget Button (appears only when chat is not expanded) -->
      <div
        *ngIf="!isChatOpen || (!isExpanded && isChatOpen)"
        class="chat-bot-bubble"
        (click)="openChat()"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path
            d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
          ></path>
        </svg>
      </div>

      <!-- Main Chat Window -->
      <div
        *ngIf="isChatOpen"
        class="chat-window"
        [ngClass]="{ expanded: isExpanded }"
      >
        <app-chat
          (close)="closeChat()"
          (expandStateChange)="handleExpandStateChange($event)"
        >
        </app-chat>
      </div>
    </div>
  `,
  styles: [
    `
      .chat-container-wrapper {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
      }

      .chat-bot-bubble {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background-color: #007bff;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s, box-shadow 0.2s;
        color: white;
      }

      .chat-bot-bubble:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.25);
      }

      .chat-window {
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 350px;
        height: 500px;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
      }

      .chat-window.expanded {
        width: 70vw;
        height: 70vh;
        bottom: 50%;
        right: 50%;
        transform: translate(50%, 50%);
      }
    `,
  ],
})
export class ChatWrapperComponent {
  isChatOpen = false;
  isExpanded = false;

  openChat(): void {
    this.isChatOpen = true;
  }

  closeChat(): void {
    this.isChatOpen = false;
    this.isExpanded = false;
  }

  handleExpandStateChange(expanded: boolean): void {
    this.isExpanded = expanded;
  }
}
