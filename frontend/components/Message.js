import React from 'react';
import ReactMarkdown from 'react-markdown';

const ToolCard = ({ type, name, data }) => {
  const isToolCall = type === 'tool_call';
  const isToolResponse = type === 'tool_response';
  
  const bgColor = isToolCall 
    ? 'bg-blue-50 border-blue-200' 
    : 'bg-green-50 border-green-200';
  
  let content = null;
  
  if (isToolCall) {
    content = (
      <>
        <div className="font-semibold text-blue-700">Tool Call: {name}</div>
        <pre className="mt-1 text-xs overflow-x-auto p-2 bg-gray-100 rounded">
          {JSON.stringify(data, null, 2)}
        </pre>
      </>
    );
  } else if (isToolResponse) {
    content = (
      <>
        <div className="font-semibold text-green-700">Tool Response: {name}</div>
        <pre className="mt-1 text-xs overflow-x-auto p-2 bg-gray-100 rounded">
          {JSON.stringify(data, null, 2)}
        </pre>
      </>
    );
  }
  
  return (
    <div className={`p-2 mt-2 mb-2 rounded border ${bgColor}`}>
      {content}
    </div>
  );
};

const Message = ({ message, conversation, isUser }) => {
  if (isUser) {
    return (
      <div className="chat-message user-message">
        <div className="font-bold mb-1">You</div>
        <div>{message}</div>
      </div>
    );
  }
  
  return (
    <div className="chat-message assistant-message">
      <div className="font-bold mb-1">Assistant</div>
      <ReactMarkdown>{message}</ReactMarkdown>
      
      {/* Show tool interactions if available */}
      {conversation && conversation.length > 0 && (
        <div className="mt-3 border-t pt-2 text-sm">
          <details>
            <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
              Show processing details
            </summary>
            <div className="mt-2">
              {conversation.map((item, idx) => {
                if (item.type === 'tool_call') {
                  return (
                    <ToolCard 
                      key={`tool-call-${idx}`}
                      type="tool_call"
                      name={item.name}
                      data={item.input}
                    />
                  );
                } else if (item.type === 'tool_response') {
                  return (
                    <ToolCard 
                      key={`tool-response-${idx}`}
                      type="tool_response"
                      name={item.name}
                      data={item.response}
                    />
                  );
                }
                return null;
              })}
            </div>
          </details>
        </div>
      )}
    </div>
  );
};

export default Message; 