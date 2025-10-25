"""LocalLLM_Manager - Simple and Focused

Purpose: Manage a local Ollama LLM service with GPU optimization.
Philosophy: Do one thing well - provide a clean interface to local LLM inference.

Core Responsibilities:
  1. Start Ollama service if needed (with GPU environment)
  2. Provide simple generate() interface for LLM inference
  3. Clean up only what we started

Design Principles:
  - Simple and focused on core LLM functionality
  - GPU-optimized environment when starting service
  - Non-aggressive - doesn't interfere with existing ollama processes
  - Reliable cleanup of only our own processes
"""

import logging
import os
import subprocess
import time
from typing import Any, Dict, Optional

import requests


class LocalLLMManager:
    """Simple manager for local LLM inference via Ollama API."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 11434, timeout: int = 120):
        self.host = host
        self.port = port
        self.base_url = f"http://{self.host}:{self.port}"
        self.timeout = timeout
        
        self._ollama_process = None
        self._we_started_service = False
        
        self.logger = logging.getLogger("LocalLLMManager")
    
    # ---------- Context Manager ----------
    def __enter__(self) -> "LocalLLMManager":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    # ---------- Service Management ----------
    def is_service_running(self) -> bool:
        """Check if Ollama service is responding."""
        try:
            r = requests.get(f"{self.base_url}/api/version", timeout=2)
            return r.status_code == 200
        except Exception:
            return False
    
    def start_service_if_needed(self) -> bool:
        """Start Ollama service if not already running."""
        if self.is_service_running():
            self.logger.info("Ollama service already running")
            return True
        
        self.logger.info("Starting Ollama service with GPU optimization...")
        
        # Set GPU-optimized environment
        env = os.environ.copy()
        env.update({
            'OLLAMA_FLASH_ATTENTION': '1',
            'OLLAMA_NUM_PARALLEL': '1', 
            'CUDA_VISIBLE_DEVICES': '0'
        })
        
        try:
            self._ollama_process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            
            self._we_started_service = True
            self.logger.info(f"Started Ollama service (PID: {self._ollama_process.pid})")
            
            # Wait for service to be ready
            for _ in range(30):  # 15 second timeout
                if self.is_service_running():
                    self.logger.info("Ollama service ready")
                    return True
                time.sleep(0.5)
            
            self.logger.error("Service failed to start within timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to start Ollama service: {e}")
            return False
    
    # ---------- LLM Interface ----------
    def generate(self, prompt: str, model: str = "gemma3:1b", 
                options: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Generate complete LLM response."""
        # Ensure service is running
        if not self.is_service_running():
            if not self.start_service_if_needed():
                return {"ok": False, "error": "Could not start Ollama service"}
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        if options:
            payload["options"] = options
        
        start_time = time.time()
        try:
            r = requests.post(f"{self.base_url}/api/generate", 
                            json=payload, timeout=self.timeout)
            
            if r.status_code == 200:
                data = r.json()
                return {
                    "ok": True,
                    "text": data.get("response", "").strip(),
                    "model": model,
                    "time_s": time.time() - start_time
                }
            else:
                return {
                    "ok": False,
                    "error": f"HTTP {r.status_code}: {r.text}",
                    "model": model
                }
                
        except requests.exceptions.Timeout:
            return {"ok": False, "error": f"Timeout after {self.timeout}s", "model": model}
        except Exception as e:
            return {"ok": False, "error": str(e), "model": model}
    
    def generate_stream(self, prompt: str, model: str = "gemma3:1b", 
                       options: Dict[str, Any] | None = None) -> requests.Response:
        """Return raw streaming response for end program to handle."""
        if not self.is_service_running():
            if not self.start_service_if_needed():
                raise RuntimeError("Could not start Ollama service")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }
        
        if options:
            payload["options"] = options
        
        return requests.post(f"{self.base_url}/api/generate", 
                           json=payload, stream=True, timeout=self.timeout)
    
    def get_available_models(self) -> list:
        """Get list of available models."""
        if not self.is_service_running():
            return []
        
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if r.status_code == 200:
                data = r.json()
                return [model.get("name", "") for model in data.get("models", [])]
            return []
        except Exception as e:
            self.logger.error(f"Failed to get models: {e}")
            return []
    
    # ---------- Cache & Model Management ----------
    def clear_model_cache(self, model: str = None) -> bool:
        """Clear KV cache for model (or all models if None)."""
        try:
            if model:
                # Clear specific model's cache
                requests.post(f"{self.base_url}/api/generate", 
                             json={"model": model, "prompt": "", "keep_alive": 0},
                             timeout=10)
            else:
                # Unload all models to clear all caches
                models = self.get_available_models()
                for m in models:
                    requests.post(f"{self.base_url}/api/generate",
                                 json={"model": m, "prompt": "", "keep_alive": 0},
                                 timeout=10)
            self.logger.info(f"Cleared cache for {'all models' if not model else model}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False

    def keep_model_warm(self, model: str, keep_alive: str = "5m") -> bool:
        """Keep model in memory for specified duration."""
        try:
            requests.post(f"{self.base_url}/api/generate",
                         json={"model": model, "prompt": "", "keep_alive": keep_alive},
                         timeout=10)
            self.logger.info(f"Keeping {model} warm for {keep_alive}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to keep model warm: {e}")
            return False
    
    # ---------- Cleanup ----------
    def cleanup(self):
        """Clean up only what we started, with cache clearing."""
        # Clear model caches if we started the service
        if self._we_started_service:
            self.logger.info("Clearing model caches...")
            self.clear_model_cache()  # Unload all models
        
        # Stop service if we started it
        if self._we_started_service and self._ollama_process:
            try:
                self.logger.info("Stopping Ollama service we started...")
                self._ollama_process.terminate()
                self._ollama_process.wait(timeout=10)
                self.logger.info("Ollama service stopped cleanly")
            except subprocess.TimeoutExpired:
                self.logger.warning("Force killing Ollama service...")
                self._ollama_process.kill()
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
            finally:
                self._ollama_process = None
                self._we_started_service = False


if __name__ == "__main__":
    # Simple example usage
    logging.basicConfig(level=logging.INFO)
    
    with LocalLLMManager() as mgr:
        # Test basic functionality
        print("Available models:", mgr.get_available_models())
        
        result = mgr.generate("Hello! How are you?", "gemma3:1b")
        if result["ok"]:
            print(f"Response: {result['text']}")
            print(f"Time: {result['time_s']:.2f}s")
        else:
            print(f"Error: {result['error']}")
