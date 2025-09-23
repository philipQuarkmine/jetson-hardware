# LocalLLM_Manager Integration Guide

This guide shows how other programs can integrate with `LocalLLM_Manager` for local AI capabilities.

## Overview

`LocalLLM_Manager` follows the principle: **"Good programs do clear tasks very well"**

- **Single Responsibility**: Manages Ollama service + provides streaming tools
- **Clean Architecture**: Your program handles UI concerns, manager handles service
- **Simple API**: Import, use, cleanup

## Basic Integration

### 1. Import and Setup
```python
from Managers.LocalLLM_Manager import LocalLLMManager

class MyApp:
    def __init__(self):
        self.llm = LocalLLMManager()
        
    def start(self):
        # Start the service
        success = self.llm.start_service()
        if not success:
            print("Failed to start LLM service")
            return False
        return True
        
    def cleanup(self):
        # Always call this when exiting
        self.llm.cleanup()
```

### 2. Basic Text Generation
```python
def chat(self, message, model="llama3.2:3b"):
    result = self.llm.generate(message, model)
    
    if result['ok']:
        response = result['text']
        time_taken = result['time_s']
        print(f"Response ({time_taken:.2f}s): {response}")
        return response
    else:
        error = result['error']
        print(f"Error: {error}")
        return None
```

### 3. Model Management
```python
def list_available_models(self):
    """Get list of available models"""
    models = self.llm.list_models()
    return models

def ensure_model_ready(self, model):
    """Keep model warm for instant responses"""
    self.llm.keep_model_warm(model)
    
def free_memory(self):
    """Clear model cache to free GPU memory"""
    self.llm.clear_model_cache()
```

## Streaming Integration (Real-time UI)

For responsive user interfaces, use streaming:

### 4. Streaming Responses
```python
def stream_chat(self, message, model="llama3.2:3b"):
    """Stream response word-by-word for real-time UI"""
    response_stream = self.llm.generate_stream(message, model)
    
    full_response = ""
    
    # The manager returns raw requests.Response - handle your own buffering
    for chunk in response_stream.iter_lines():
        if chunk:
            try:
                data = json.loads(chunk.decode('utf-8'))
                
                # Check if streaming is complete
                if data.get('done', False):
                    break
                    
                # Get the response chunk
                text_chunk = data.get('response', '')
                if text_chunk:
                    full_response += text_chunk
                    
                    # Handle your own UI updates
                    self.update_ui(text_chunk)  # Your UI method
                    
            except json.JSONDecodeError:
                continue
                
    return full_response

def update_ui(self, text_chunk):
    """Your custom UI update logic"""
    print(text_chunk, end='', flush=True)
```

### 5. Advanced Streaming with Word Buffering
```python
import time

class StreamingChatHandler:
    def __init__(self):
        self.word_buffer = []
        
    def stream_with_word_buffering(self, llm_manager, message, model):
        """Stream with smooth word-by-word display"""
        response_stream = llm_manager.generate_stream(message, model)
        
        for chunk in response_stream.iter_lines():
            if chunk:
                try:
                    data = json.loads(chunk.decode('utf-8'))
                    
                    if data.get('done', False):
                        self._flush_remaining_words()
                        break
                        
                    text_chunk = data.get('response', '')
                    if text_chunk:
                        self._process_chunk(text_chunk)
                        
                except json.JSONDecodeError:
                    continue
    
    def _process_chunk(self, chunk):
        """Process chunk and handle word buffering"""
        # Add to buffer
        self.word_buffer.append(chunk)
        
        # Check if we have complete words
        buffer_text = ''.join(self.word_buffer)
        
        # Look for word boundaries (space, punctuation)
        if ' ' in buffer_text or any(p in buffer_text for p in '.,!?;'):
            # Display complete words
            words = buffer_text.split(' ')
            
            # Display all but the last word (might be incomplete)
            for word in words[:-1]:
                print(word + ' ', end='', flush=True)
                time.sleep(0.05)  # Smooth display timing
            
            # Keep the last word in buffer (might be incomplete)
            self.word_buffer = [words[-1]] if words[-1] else []
    
    def _flush_remaining_words(self):
        """Display any remaining words in buffer"""
        if self.word_buffer:
            print(''.join(self.word_buffer), end='', flush=True)
            self.word_buffer = []
```

## Complete Integration Example

```python
#!/usr/bin/env python3
"""
Example: Complete integration with LocalLLM_Manager
"""

import json
import signal
import sys
from Managers.LocalLLM_Manager import LocalLLMManager

class MyAIApplication:
    def __init__(self):
        self.llm = LocalLLMManager()
        self.running = False
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\nShutting down gracefully...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def start(self):
        """Start the application"""
        print("🚀 Starting AI Application...")
        
        # Start LLM service
        if not self.llm.start_service():
            print("❌ Failed to start LLM service")
            return False
        
        # List available models
        models = self.llm.list_models()
        if not models:
            print("❌ No models available")
            return False
            
        print(f"✅ Available models: {models}")
        
        # Keep a model warm for responsiveness
        default_model = models[0]
        self.llm.keep_model_warm(default_model)
        print(f"🔥 Warmed up model: {default_model}")
        
        self.running = True
        return True
    
    def chat_loop(self):
        """Interactive chat loop"""
        model = "llama3.2:3b"  # Choose your preferred model
        
        while self.running:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['/quit', '/exit']:
                    break
                    
                if user_input.lower() == '/stream':
                    # Streaming example
                    print(f"🤖 {model} (streaming): ", end='', flush=True)
                    self.stream_response(user_input, model)
                else:
                    # Regular response
                    print(f"🤔 {model} is thinking...")
                    result = self.llm.generate(user_input, model)
                    
                    if result['ok']:
                        print(f"🤖 {model} ({result['time_s']:.2f}s):")
                        print(result['text'])
                    else:
                        print(f"❌ Error: {result['error']}")
                        
            except KeyboardInterrupt:
                break
            except EOFError:
                break
    
    def stream_response(self, message, model):
        """Example streaming response"""
        response_stream = self.llm.generate_stream(message, model)
        
        for chunk in response_stream.iter_lines():
            if chunk:
                try:
                    data = json.loads(chunk.decode('utf-8'))
                    
                    if data.get('done', False):
                        print()  # New line at end
                        break
                        
                    text_chunk = data.get('response', '')
                    if text_chunk:
                        print(text_chunk, end='', flush=True)
                        
                except json.JSONDecodeError:
                    continue
    
    def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up...")
        self.llm.cleanup()

# Usage example
if __name__ == "__main__":
    app = MyAIApplication()
    
    if app.start():
        try:
            app.chat_loop()
        except Exception as e:
            print(f"💥 Error: {e}")
        finally:
            app.cleanup()
    else:
        print("Failed to start application")
```

## Error Handling

```python
def robust_generate(self, message, model, max_retries=3):
    """Generate with retry logic"""
    for attempt in range(max_retries):
        try:
            result = self.llm.generate(message, model)
            
            if result['ok']:
                return result
            else:
                print(f"Attempt {attempt + 1} failed: {result['error']}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(1)
                    
        except Exception as e:
            print(f"Exception on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                
    return {'ok': False, 'error': 'Max retries exceeded'}
```

## Performance Tips

1. **Model Warming**: Use `keep_model_warm()` for frequently used models
2. **Memory Management**: Call `clear_model_cache()` when switching contexts
3. **Streaming**: Use `generate_stream()` for real-time user interfaces
4. **Cleanup**: Always call `cleanup()` when exiting
5. **Error Handling**: Implement retry logic for production use

## Integration Checklist

- ✅ Import `LocalLLM_Manager`
- ✅ Call `start_service()` before use
- ✅ Call `cleanup()` when exiting
- ✅ Handle streaming responses in your UI
- ✅ Implement proper error handling
- ✅ Use model warming for performance
- ✅ Clear cache when needed
- ✅ Handle keyboard interrupts gracefully

## Architecture Benefits

By using `LocalLLM_Manager`, your program gets:

- **Service Management**: Automatic Ollama service handling
- **Streaming Support**: Real-time response capabilities  
- **Performance Tools**: Model warming and cache management
- **Clean Separation**: Focus on your UI/logic, not service management
- **Reliability**: Tested, stable AI service integration

---

**Ready to build intelligent applications with local AI! 🚀**