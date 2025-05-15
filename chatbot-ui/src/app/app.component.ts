import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatComponent } from './chat/chat.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, ChatComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  title = 'chatbot-ui';
  isChatOpen = false;
  isChatExpanded = false;

  toggleChat(): void {
    if (this.isChatOpen) {
      this.isChatOpen = false;
      this.isChatExpanded = false;
    } else {
      this.isChatOpen = true;
    }
  }

  handleCloseChat(): void {
    this.isChatOpen = false;
    this.isChatExpanded = false;
  }

  handleToggleExpand(state: boolean): void {
    this.isChatExpanded = state;
  }
}
