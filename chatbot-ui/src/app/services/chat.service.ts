import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, map, throwError } from 'rxjs';
import { Message } from '../models/chat.model';

interface RasaResponse {
  recipient_id: string;
  text?: string;
  image?: string;
}

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  private apiUrl = 'http://localhost:5005/webhooks/rest/webhook';
  private messages: Message[] = [];

  constructor(private http: HttpClient) {}

  sendMessage(message: string): Observable<Message[]> {
    const payload = { sender: 'user', message };
    this.addMessage({
      content: message,
      sender: 'user',
      timestamp: new Date(),
    });
    return this.http.post<RasaResponse[]>(this.apiUrl, payload).pipe(
      map(
        (responses) =>
          responses.map((r) => ({
            content: r.text ?? '',
            sender: 'bot',
            timestamp: new Date(),
          })) as Message[]
      ),
      map((botMessages) => {
        botMessages.forEach((m) => this.addMessage(m));
        return botMessages;
      }),
      catchError(this.handleError)
    );
  }

  private handleError(error: HttpErrorResponse) {
    return throwError(() => error);
  }

  addMessage(message: Message) {
    this.messages.push(message);
  }

  getMessages(): Message[] {
    return this.messages;
  }

  clearMessages() {
    this.messages = [];
  }
}
