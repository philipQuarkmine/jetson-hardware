"""
Local LLM Manager for Jetson Systems
Manages Ollama service and multiple LLM models with acquire/release patterns
similar to other hardware managers in the system.
"""

import os
import subprocess
import time
import threading
import logging
import signal
import fcntl
import requests
import json
from typing import Dict, Optional, List, Any
from pathlib import Path


class LocalLLMManager:
    """
    Manages local LLM inference via Ollama with support for multiple models.
    Follows same acquire/release pattern as other hardware managers.
    """
    
    # Lock file for ensuring single instance
    LOCK_FILE = "/tmp/local_llm_manager.lock"
    
    # Default Ollama configuration
    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 11434
    
    # Model configurations for different tasks
    MODEL_CONFIGS = {
        "motor_control": {
            "model": "llama3.2:1b",
            "description": "Fast, lightweight model for robot motor commands",
            "options": {
                "temperature": 0.1,
                "max_tokens": 20,
                "top_p": 0.9
            }
        },
        "conversation": {
            "model": "llama3.2:1b", 
            "description": "General conversation and complex reasoning",
            "options": {
                "temperature": 0.7,
                "max_tokens": 512,
                "top_p": 0.9
            }
        },
        "code_analysis": {
            "model": "llama3.2:1b",  # Will upgrade to code model later
            "description": "Code analysis and generation",
            "options": {
                "temperature": 0.2,
                "max_tokens": 1024,
                "top_p": 0.95
            }
        }
    }
    
    def __init__(self, host: str = None, port: int = None, auto_start: bool = True):
        """
        Initialize LLM Manager
        
        Args:
            host: Ollama host (default: 127.0.0.1)
            port: Ollama port (default: 11434)
            auto_start: Whether to auto-start Ollama if not running
        """
        self.host = host or self.DEFAULT_HOST
        self.port = port or self.DEFAULT_PORT
        self.base_url = f"http://{self.host}:{self.port}"
        self.auto_start = auto_start
        
        # Service management
        self.ollama_process = None
        self.is_acquired = False
        self.lock_file_handle = None
        
        # Model cache
        self.loaded_models = set()
        self.available_models = []
        
        # Logging
        self.logger = logging.getLogger(f"LocalLLMManager_{id(self)}")
        
        self.logger.info(f"LocalLLMManager initialized - {self.base_url}")
    
    def acquire(self) -> bool:
        """
        Acquire LLM manager with exclusive lock (similar to other managers)
        
        Returns:
            bool: True if successfully acquired, False otherwise
        """
        try:
            # Try to acquire lock file
            self.lock_file_handle = open(self.LOCK_FILE, 'w')
            fcntl.flock(self.lock_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write our PID to lock file
            self.lock_file_handle.write(str(os.getpid()))
            self.lock_file_handle.flush()
            
            self.logger.info("Lock acquired for LocalLLMManager")
            
            # Check if Ollama is running
            if not self._is_ollama_running():
                if self.auto_start:
                    self.logger.info("Ollama not running - starting service...")
                    if not self._start_ollama_service():
                        self.logger.error("Failed to start Ollama service")
                        self.release()
                        return False
                else:
                    self.logger.error("Ollama not running and auto_start=False")
                    self.release()
                    return False
            
            # Wait for service to be ready
            if not self._wait_for_service():
                self.logger.error("Ollama service failed to become ready")
                self.release()
                return False
            
            # Load available models
            self._refresh_available_models()
            
            # Ensure required models are available
            if not self._ensure_required_models():
                self.logger.warning("Some required models are not available")
            
            self.is_acquired = True
            self.logger.info("LocalLLMManager acquired successfully")
            return True
            
        except (IOError, OSError) as e:
            self.logger.warning(f"Could not acquire lock: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to acquire LocalLLMManager: {e}")
            self.release()
            return False
    
    def release(self):
        """Release LLM manager and clean up resources"""
        try:
            self.is_acquired = False
            
            # Stop Ollama service if we started it
            if self.ollama_process:
                self.logger.info("Stopping Ollama service...")
                self._stop_ollama_service()
            
            # Release lock
            if self.lock_file_handle:
                fcntl.flock(self.lock_file_handle.fileno(), fcntl.LOCK_UN)
                self.lock_file_handle.close()
                self.lock_file_handle = None
                
                # Clean up lock file
                try:
                    os.unlink(self.LOCK_FILE)
                except:
                    pass
            
            self.logger.info("LocalLLMManager released")
            
        except Exception as e:
            self.logger.error(f"Error during LocalLLMManager release: {e}")
    
    def generate(self, prompt: str, task_type: str = "motor_control", 
                 model: str = None, options: Dict = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Generate response using specified model configuration
        
        Args:
            prompt: Input prompt
            task_type: Type of task (motor_control, conversation, code_analysis)
            model: Override model name (optional)
            options: Override generation options (optional)
            timeout: Request timeout in seconds
            
        Returns:
            Dict with response, model info, and timing
        """
        if not self.is_acquired:
            raise RuntimeError("LocalLLMManager not acquired - call acquire() first")
        
        # Get model configuration
        config = self.MODEL_CONFIGS.get(task_type, self.MODEL_CONFIGS["motor_control"])
        model_name = model or config["model"]
        gen_options = options or config["options"]
        
        start_time = time.time()
        
        try:
            # Ensure model is loaded
            if model_name not in self.loaded_models:
                self._load_model(model_name)
            
            # Make API request
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": gen_options
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                end_time = time.time()
                
                return {
                    "success": True,
                    "response": result.get("response", "").strip(),
                    "model": model_name,
                    "task_type": task_type,
                    "timing": {
                        "duration": end_time - start_time,
                        "eval_count": result.get("eval_count", 0),
                        "eval_duration": result.get("eval_duration", 0) / 1_000_000_000  # Convert to seconds
                    },
                    "context": result.get("context", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "model": model_name,
                    "task_type": task_type
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"Request timeout after {timeout}s",
                "model": model_name,
                "task_type": task_type
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model_name,
                "task_type": task_type
            }
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        return self.available_models.copy()
    
    def get_task_types(self) -> List[str]:
        """Get list of configured task types"""
        return list(self.MODEL_CONFIGS.keys())
    
    def add_model_config(self, task_type: str, model: str, description: str, options: Dict):
        """Add new model configuration for a task type"""
        self.MODEL_CONFIGS[task_type] = {
            "model": model,
            "description": description,
            "options": options.copy()
        }
        self.logger.info(f"Added model config: {task_type} -> {model}")
    
    def _is_ollama_running(self) -> bool:
        """Check if Ollama service is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _start_ollama_service(self) -> bool:
        """Start Ollama service in background"""
        try:
            # Check if already running
            if self._is_ollama_running():
                self.logger.info("Ollama already running")
                return True
            
            # Start Ollama serve in background
            self.ollama_process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.logger.info(f"Started Ollama service (PID: {self.ollama_process.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Ollama service: {e}")
            return False
    
    def _stop_ollama_service(self):
        """Stop Ollama service if we started it"""
        if self.ollama_process:
            try:
                # Send SIGTERM to process group
                os.killpg(os.getpgid(self.ollama_process.pid), signal.SIGTERM)
                
                # Wait for graceful shutdown
                try:
                    self.ollama_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if not stopped
                    os.killpg(os.getpgid(self.ollama_process.pid), signal.SIGKILL)
                    self.ollama_process.wait()
                
                self.logger.info("Ollama service stopped")
                self.ollama_process = None
                
            except Exception as e:
                self.logger.error(f"Error stopping Ollama service: {e}")
    
    def _wait_for_service(self, max_wait: int = 30) -> bool:
        """Wait for Ollama service to be ready"""
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if self._is_ollama_running():
                self.logger.info("Ollama service is ready")
                return True
            time.sleep(0.5)
        
        self.logger.error(f"Ollama service not ready after {max_wait}s")
        return False
    
    def _refresh_available_models(self):
        """Refresh list of available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.available_models = data.get("models", [])
                self.logger.info(f"Found {len(self.available_models)} available models")
            else:
                self.logger.warning("Could not fetch available models")
                self.available_models = []
        except Exception as e:
            self.logger.error(f"Error fetching available models: {e}")
            self.available_models = []
    
    def _ensure_required_models(self) -> bool:
        """Ensure all required models are available"""
        required_models = set()
        for config in self.MODEL_CONFIGS.values():
            required_models.add(config["model"])
        
        available_names = {model["name"] for model in self.available_models}
        missing_models = required_models - available_names
        
        if missing_models:
            self.logger.warning(f"Missing models: {missing_models}")
            self.logger.warning("Run 'ollama pull <model>' to download missing models")
            return False
        
        return True
    
    def _load_model(self, model_name: str):
        """Load model into memory (first request loads it automatically)"""
        try:
            # Make a simple request to load the model
            payload = {
                "model": model_name,
                "prompt": "test",
                "stream": False,
                "options": {"max_tokens": 1}
            }
            
            requests.post(f"{self.base_url}/api/generate", json=payload, timeout=30)
            self.loaded_models.add(model_name)
            self.logger.info(f"Model loaded: {model_name}")
            
        except Exception as e:
            self.logger.warning(f"Could not pre-load model {model_name}: {e}")


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test LLM Manager
    llm_manager = LocalLLMManager()
    
    if llm_manager.acquire():
        print("✅ LLM Manager acquired successfully")
        
        # Test motor control task
        result = llm_manager.generate(
            prompt="move forward", 
            task_type="motor_control"
        )
        
        if result["success"]:
            print(f"🤖 Motor Control Response: {result['response']}")
            print(f"⏱️  Timing: {result['timing']['duration']:.2f}s")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Test conversation task
        result = llm_manager.generate(
            prompt="What is the weather like?",
            task_type="conversation"
        )
        
        if result["success"]:
            print(f"💬 Conversation Response: {result['response'][:100]}...")
        
        # Show available models
        models = llm_manager.list_available_models()
        print(f"📋 Available models: {[m['name'] for m in models]}")
        
        llm_manager.release()
        print("✅ LLM Manager released")
    else:
        print("❌ Failed to acquire LLM Manager")