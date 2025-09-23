#!/usr/bin/env python3
"""Interactive LLM Chat Program with Streaming Support using LocalLLM_Manager.

A snappy command-line interface that allows you to:
- Choose from available LLM models
- See streaming responses in real-time with word-level buffering
- Enter your own prompts interactively
- See response times and model information
- Exit gracefully with cleanup
"""

import json
import os
import sys
import time
import logging

# Add the parent directory to import our manager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from Managers.LocalLLM_Manager import LocalLLMManager


class StreamingChatHandler:
    """Handles streaming responses with word-level buffering for smooth display."""
    
    def __init__(self):
        self.word_buffer = ""
        
    def stream_response(self, manager, prompt, model):
        """Handle streaming with word-level buffering for smooth display."""
        try:
            response = manager.generate_stream(prompt, model)
            
            print(f"🤖 {model}: ", end='', flush=True)
            
            full_response = ""
            start_time = time.time()
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk_data = json.loads(line)
                        
                        if 'response' in chunk_data:
                            chunk_text = chunk_data['response']
                            full_response += chunk_text
                            self._process_chunk(chunk_text)
                            
                        # Check if generation is done
                        if chunk_data.get('done', False):
                            self._flush_buffer()
                            break
                            
                    except json.JSONDecodeError:
                        continue  # Skip invalid JSON lines
            
            elapsed = time.time() - start_time
            print(f"\n   ⏱️  {elapsed:.2f}s")
            
            return {
                "ok": True,
                "text": full_response,
                "time_s": elapsed,
                "model": model
            }
                        
        except Exception as e:
            print(f"\n❌ Streaming error: {e}")
            return {
                "ok": False,
                "error": str(e),
                "model": model
            }
            
    def _process_chunk(self, chunk):
        """Process chunk with word-level buffering."""
        self.word_buffer += chunk
        
        # Split on spaces to get complete words
        words = self.word_buffer.split(' ')
        
        # Display all complete words (all but the last)
        for word in words[:-1]:
            print(word + ' ', end='', flush=True)
        
        # Keep the last partial word in buffer
        self.word_buffer = words[-1]
        
        # If the chunk ends with punctuation, flush the buffer
        if chunk and chunk[-1] in '.!?\n':
            self._flush_buffer()
    
    def _flush_buffer(self):
        """Flush any remaining text in buffer."""
        if self.word_buffer.strip():
            print(self.word_buffer, end='', flush=True)
            self.word_buffer = ""


class InteractiveLLMChat:
    """Interactive chat interface for LocalLLM_Manager with streaming support."""
    
    def __init__(self):
        self.manager = None
        self.current_model = None
        self.chat_history = []
        self.streaming_handler = StreamingChatHandler()
        self.use_streaming = True
    
    def print_banner(self):
        """Print welcome banner."""
        print("=" * 60)
        print("🚀 Interactive LLM Chat - Streaming Edition")
        print("=" * 60)
        print("Commands:")
        print("  /models    - List available models")
        print("  /switch    - Switch to different model")
        print("  /stream    - Toggle streaming mode on/off")
        print("  /history   - Show chat history")
        print("  /clear     - Clear chat history")
        print("  /help      - Show this help")
        print("  /quit      - Exit the program")
        print("=" * 60)
    
    def list_models(self):
        """List available models."""
        models = self.manager.get_available_models()
        if models:
            print("\n📋 Available Models:")
            for i, model in enumerate(models, 1):
                current = " (current)" if model == self.current_model else ""
                print(f"  {i}. {model}{current}")
            return models
        else:
            print("\n❌ No models available")
            return []
    
    def choose_model(self):
        """Let user choose a model."""
        models = self.list_models()
        if not models:
            return None
        
        while True:
            try:
                print(f"\nCurrent model: {self.current_model or 'None'}")
                choice = input("Enter model number (or press Enter to keep current): ").strip()
                
                if not choice and self.current_model:
                    return self.current_model
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(models):
                        return models[idx]
                    else:
                        print(f"❌ Please enter a number between 1 and {len(models)}")
                else:
                    print("❌ Please enter a valid number")
                    
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Cancelled model selection")
                return self.current_model
    
    def show_history(self):
        """Show chat history."""
        if not self.chat_history:
            print("\n📝 No chat history yet")
            return
        
        print(f"\n📝 Chat History ({len(self.chat_history)} entries):")
        print("-" * 50)
        for i, entry in enumerate(self.chat_history, 1):
            model = entry['model']
            prompt = entry['prompt']
            response = entry['response']
            time_s = entry['time_s']
            
            print(f"{i}. [{model}] ({time_s:.2f}s)")
            print(f"   Q: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")
            print(f"   A: {response[:60]}{'...' if len(response) > 60 else ''}")
            print()
    
    def clear_history(self):
        """Clear chat history."""
        self.chat_history.clear()
        print("\n🗑️  Chat history cleared")
    
    def toggle_streaming(self):
        """Toggle streaming mode."""
        self.use_streaming = not self.use_streaming
        status = "enabled" if self.use_streaming else "disabled"
        print(f"\n🌊 Streaming mode {status}")
    
    def show_help(self):
        """Show help information."""
        stream_status = "enabled" if self.use_streaming else "disabled"
        print(f"\n❓ Help:")
        print(f"  • Streaming mode: {stream_status}")
        print("  • Type your prompt and press Enter to chat with the LLM")
        print("  • Use /commands to control the program")
        print("  • Press Ctrl+C or type /quit to exit")
        print("  • The manager automatically handles service startup/shutdown")
        print("  • Response times and model info are shown with each response")
    
    def process_command(self, user_input):
        """Process special commands."""
        command = user_input.lower().strip()
        
        if command == "/models":
            self.list_models()
            return True
        elif command == "/switch":
            new_model = self.choose_model()
            if new_model and new_model != self.current_model:
                self.current_model = new_model
                # Keep new model warm for responsive interaction
                self.manager.keep_model_warm(self.current_model, "10m")
                print(f"✅ Switched to model: {self.current_model}")
            return True
        elif command == "/stream":
            self.toggle_streaming()
            return True
        elif command == "/history":
            self.show_history()
            return True
        elif command == "/clear":
            self.clear_history()
            return True
        elif command == "/help":
            self.show_help()
            return True
        elif command in ["/quit", "/exit", "/q"]:
            print("\n👋 Goodbye!")
            return False
        else:
            return None  # Not a command
    
    def run_chat(self):
        """Main chat loop."""
        try:
            with LocalLLMManager() as mgr:
                self.manager = mgr
                
                # Initialize
                print("\n🚀 Starting LLM service...")
                if not mgr.start_service_if_needed():
                    print("❌ Failed to start LLM service")
                    return
                
                # Choose initial model
                print("\n🎯 Choose your LLM model:")
                self.current_model = self.choose_model()
                if not self.current_model:
                    print("❌ No model selected. Exiting.")
                    return
                
                # Keep model warm for responsive interaction
                mgr.keep_model_warm(self.current_model, "10m")
                
                print(f"\n✅ Ready to chat with {self.current_model}!")
                print(f"🌊 Streaming mode: {'enabled' if self.use_streaming else 'disabled'}")
                print("💡 Type your prompt or use /help for commands")
                
                # Main chat loop
                while True:
                    try:
                        # Get user input
                        user_input = input(f"\n💬 You: ").strip()
                        
                        if not user_input:
                            continue
                        
                        # Check for commands
                        command_result = self.process_command(user_input)
                        if command_result is False:  # Quit command
                            break
                        elif command_result is True:  # Other command processed
                            continue
                        
                        # Regular chat
                        if not self.current_model:
                            print("❌ No model selected. Use /switch to choose a model.")
                            continue
                        
                        # Generate response
                        if self.use_streaming:
                            result = self.streaming_handler.stream_response(
                                mgr, user_input, self.current_model)
                        else:
                            print(f"🤔 {self.current_model} is thinking...")
                            result = mgr.generate(user_input, self.current_model)
                            
                            if result.get('ok'):
                                response_text = result.get('text', '')
                                time_taken = result.get('time_s', 0)
                                print(f"\n🤖 {self.current_model} ({time_taken:.2f}s):")
                                print(response_text)
                        
                        if result.get('ok'):
                            # Add to history
                            self.chat_history.append({
                                'model': self.current_model,
                                'prompt': user_input,
                                'response': result.get('text', ''),
                                'time_s': result.get('time_s', 0)
                            })
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            print(f"\n❌ Error: {error_msg}")
                    
                    except KeyboardInterrupt:
                        print("\n\n👋 Interrupted. Exiting...")
                        break
                    except EOFError:
                        print("\n👋 EOF received. Exiting...")
                        break
                
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")
        finally:
            print("\n🧹 Cleaning up...")


def main():
    """Main function."""
    # Set up minimal logging
    logging.basicConfig(level=logging.WARNING)  # Only show warnings/errors
    
    # Create and run chat interface
    chat = InteractiveLLMChat()
    chat.print_banner()
    
    try:
        chat.run_chat()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
    
    print("✨ Thanks for using Interactive LLM Chat!")


if __name__ == "__main__":
    main()