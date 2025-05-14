import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import { ChatRequest, ChatResponse, Message } from '../models/chat.model';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = 'http://127.0.0.1:8000/chat';
  private messages: Message[] = [];

  constructor(private http: HttpClient) { }

  sendMessage(message: string): Observable<ChatResponse> {
    // Prepare the conversation context from previous messages
    const conversation_context = this.getConversationContext();
    
    const request: ChatRequest = {
      question: message,
      conversation_context: conversation_context
    };

    // Add user message to the messages array
    this.addMessage({
      content: message,
      sender: 'user',
      timestamp: new Date()    });

    return this.http.post<ChatResponse>(this.apiUrl, request)
      .pipe(
        catchError(this.handleError)
      );
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An unknown error occurred';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
    }
    
    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }

  addMessage(message: Message): void {
    this.messages.push(message);
  }

  getMessages(): Message[] {
    return this.messages;
  }

  private getConversationContext() {
    const context: { question: string; answer: string }[] = [];
    
    // Group messages by user-bot pairs
    for (let i = 0; i < this.messages.length - 1; i += 2) {
      if (i + 1 < this.messages.length) {
        const userMessage = this.messages[i];
        const botMessage = this.messages[i + 1];
        
        if (userMessage.sender === 'user' && botMessage.sender === 'bot') {
          context.push({
            question: userMessage.content,
            answer: botMessage.content
          });
        }
      }
    }
    
    return context;
  }

  clearMessages(): void {
    this.messages = [];
  }
}
