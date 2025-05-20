import React, { useState, useRef, useEffect } from 'react';
import Message from './Message';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Add user message to chat
    const userMessage = inputValue;
    setMessages((prevMessages) => [
      ...prevMessages,
      { content: userMessage, isUser: true }
    ]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Use the direct API URL when in browser
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: userMessage }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      // Process SSE response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let currentAssistantMessage = '';
      let currentConversation = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        console.log('Received chunk:', chunk);
        const events = chunk.split('\n\n').filter(e => e.trim().startsWith('data:'));
        
        for (const eventText of events) {
          if (!eventText.startsWith('data:')) continue;
          
          try {
            const event = JSON.parse(eventText.slice(5).trim());
            console.log('Parsed event:', event);
            
            switch (event.type) {
              case 'start':
                // Clear any previous conversation for new stream
                currentAssistantMessage = '';
                currentConversation = [];
                break;
                
              case 'assistant_message':
                currentAssistantMessage = event.content;
                currentConversation.push({
                  type: 'assistant_message',
                  content: currentAssistantMessage
                });
                break;
                
              case 'tool_call':
                currentConversation.push({
                  type: 'tool_call',
                  name: event.name,
                  input: event.input
                });
                break;
                
              case 'tool_response':
                currentConversation.push({
                  type: 'tool_response',
                  name: event.name,
                  response: event.response
                });
                break;
                
              case 'end':
                // Stream completed, update the message to be complete
                break;
            }
            
            // Update the messages state with the current conversation
            setMessages((prevMessages) => {
              const newMessages = [...prevMessages];
              // Find any existing assistant response for this conversation
              const assistantIndex = newMessages.findIndex(
                (msg) => msg.isAssistantResponse && !msg.isCompleted
              );
              
              if (assistantIndex >= 0) {
                // Update existing assistant response
                newMessages[assistantIndex].content = currentAssistantMessage;
                newMessages[assistantIndex].conversation = currentConversation;
                if (event.type === 'end') {
                  newMessages[assistantIndex].isCompleted = true;
                }
              } else if (currentConversation.length > 0) {
                // Add new assistant response
                newMessages.push({
                  content: currentAssistantMessage,
                  conversation: currentConversation,
                  isUser: false,
                  isAssistantResponse: true,
                  isCompleted: event.type === 'end'
                });
              }
              
              return newMessages;
            });
          } catch (error) {
            console.error('Error parsing SSE event:', error);
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages((prevMessages) => [
        ...prevMessages,
        { 
          content: 'Sorry, there was an error processing your request. Please try again.',
          isUser: false,
          isCompleted: true
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="message-list">
        {messages.map((message, index) => (
          <Message 
            key={index} 
            message={message.content}
            conversation={message.conversation}
            isUser={message.isUser} 
          />
        ))}
        {isLoading && (
          <div className="chat-message assistant-message">
            <div className="font-bold mb-1">Assistant</div>
            <div>Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex">
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            className="message-input"
            placeholder="Ask a question about HDB resale prices..."
            disabled={isLoading}
          />
          <button
            type="submit"
            className="ml-2 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:bg-blue-300"
            disabled={isLoading || !inputValue.trim()}
          >
            Send
          </button>
        </div>
      </form>
      <div className="text-center text-xs text-gray-400 pb-2">
        © 2025 HDB Price Analysis System · Created by wongjingping@gmail.com
      </div>
    </div>
  );
};

export default Chat; 