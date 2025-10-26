#!/usr/bin/env python3
"""
heartbeat_screensaver.py

Organic heartbeat screensaver for Jetson display.
Features a dramatically pulsing anatomical heart with dynamic arterial energy network.

Features:
- Anatomical heart shape using parametric equations
- Natural rhythm variations (resting, active, energetic states)
- Heart pulses from 50px (tiny) to 492px (nearly full screen)
- Dynamic arterial network with varied colors (7 green variations)
- Energy particles with varied colors that flow and create paths
- Pathfinder particles that create new arterial routes organically
- Paths fade smoothly from their color to background (no black artifacts)
- Decentralized spawning within 2cm area around heart center
- Soft green background (15, 35, 20) with subtle variations
- Low brightness for peaceful ambient display
- 15 FPS smooth animation with selective redrawing

Technical Details:
- Heart size: 50-492 pixel radius (dynamically calculated from display size)
- Rhythm variation: 0.15 Hz slow state changes (resting/active/energetic)
- Beat speed: 0.6 Hz with dual-chamber simulation (primary + secondary pulse)
- Arterial colors: 7 variants (forest, bright, blue-green, yellow-green, teal, olive, jade)
- Energy colors: 7 variants matching arterial palette
- Path lifecycle: 2-5 particles per path before fading
- Gradual spawning: 2 particles every 1.5s for organic growth

Usage:
    python3 SimpleTests/heartbeat_screensaver.py
    
Press Ctrl+C to exit gracefully.
"""

import math
import random
import signal
import sys
import time
from typing import List, Tuple

sys.path.append('/home/phiip/workspace/jetson-hardware')

from Managers.Display_Manager import DisplayManager


class HeartbeatScreensaver:
    """
    Organic heartbeat screensaver with flowing arterial networks.
    
    Features:
    - Abstract pulsing heart shape with soft edges
    - Textured surfaces using noise functions
    - Arterial network with energy flow particles
    - Peaceful color palette with organic feel
    """
    
    def __init__(self):
        self.display = DisplayManager()
        self.running = False
        self.start_time = time.time()
        
        # Heart parameters - natural dramatic pulsing with rhythm variation
        self.heart_beat_speed = 0.6  # Base rhythm speed
        self.heart_min_size = 50   # Minimum heart radius (resting state)
        self.heart_max_size = 492  # Maximum heart radius (20px from screen edge)
        self.heart_amplitude = self.heart_max_size - self.heart_min_size  # 442 pixels range
        
        # Natural rhythm variation (simulates resting/active/energetic states)
        self.rhythm_variation_speed = 0.15  # Slow rhythm state changes
        self.last_rhythm_change = 0
        self.rhythm_state = 0.7  # Start in moderate state (0.5=resting, 1.0=energetic)
        
        # Dynamic arterial network parameters
        self.energy_flow_speed = 0.4  # Speed of energy particles
        self.max_arteries = 30  # Maximum concurrent arteries
        self.base_particle_count = 50  # Total energy particles
        
        # Gradual spawning system
        self.spawn_interval = 1.5  # Faster spawning to see effects sooner
        self.last_spawn_time = 0
        self.particles_per_spawn = 2  # Fewer particles per spawn
        self.spawn_radius = 40  # ~2cm diameter spawning area (pixels)
        
        # Dynamic path system
        self.dynamic_arteries = {}  # Dict of artery_id -> {path, usage_count, max_usage}
        self.next_artery_id = 0
        self.particles_needing_paths = []  # Particles waiting for new paths
        self.dormant_particles = []  # Particles waiting to be spawned
        
        # Selective redrawing for smooth animation
        self.prev_heart_size = 0
        self.prev_arteries_drawn = False
        self.background_initialized = False
        
                # Color palette - soft, organic colors with variations
        self.background_green = (15, 35, 20)  # Soft green background
        self.heart_pink_base = (95, 55, 75)  # More pinkish heart color
        
        # Base colors for arterial network variations
        self.artery_base_color = (25, 45, 25)  # Base green for arteries
        self.energy_base_color = (60, 80, 40)  # Base energy color
        
        # Color variation palettes for organic diversity
        self.artery_color_variants = [
            (25, 45, 25),   # Forest green
            (35, 55, 30),   # Brighter green
            (20, 40, 35),   # Blue-green
            (30, 50, 20),   # Yellow-green
            (15, 35, 40),   # Teal
            (40, 45, 25),   # Olive green
            (25, 50, 35),   # Jade green
        ]
        
        self.energy_color_variants = [
            (60, 80, 40),   # Base green energy
            (70, 90, 45),   # Bright green
            (50, 75, 55),   # Blue-green energy
            (65, 85, 30),   # Yellow-green energy
            (45, 70, 60),   # Teal energy
            (75, 80, 40),   # Olive energy
            (55, 85, 50),   # Jade energy
        ]
        
        # Display properties
        self.width = 1280
        self.height = 1024
        self.center_x = self.width // 2
        self.center_y = self.height // 2
        
        # Arterial network - pre-calculated paths
        self.arteries = []
        self.energy_particles = []
        self.next_particle_id = 0  # For generating unique particle IDs
        
    def setup_signal_handlers(self):
        """Setup graceful exit on Ctrl+C."""
        def signal_handler(signum, frame):
            print("\n💚 Heartbeat screensaver stopping gracefully...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def create_dynamic_artery_path(self, start_angle: float = None, spawn_point: Tuple[float, float] = None) -> List[Tuple[int, int]]:
        """Generate arterial path that always moves away from center like a worm."""
        if start_angle is None:
            start_angle = random.uniform(0, 2 * math.pi)
        
        points = []
        
        # Starting position - decentralized spawning area
        if spawn_point:
            current_x, current_y = spawn_point
        else:
            # Random spawn point within 2cm diameter circle
            spawn_distance = random.uniform(0, self.spawn_radius)
            spawn_angle = random.uniform(0, 2 * math.pi)
            current_x = float(self.center_x + math.cos(spawn_angle) * spawn_distance)
            current_y = float(self.center_y + math.sin(spawn_angle) * spawn_distance)
        current_angle = start_angle
        
        # Path characteristics
        meander_intensity = random.uniform(0.1, 0.3)  # How much it can deviate
        step_size_base = random.uniform(4, 8)
        
        # Track distance from center to ensure we always move outward
        prev_distance_from_center = 0
        
        for step in range(150):  # Maximum steps before stopping
            # Add organic meandering, but constrained to not double back
            angle_change = random.uniform(-meander_intensity, meander_intensity)
            
            # Test the new direction
            test_angle = current_angle + angle_change
            test_step_size = step_size_base + random.uniform(-1, 2)
            
            # Calculate potential new position
            new_x = current_x + math.cos(test_angle) * test_step_size
            new_y = current_y + math.sin(test_angle) * test_step_size
            
            # Calculate distance from heart center (0,0 in heart coordinates)
            heart_relative_x = new_x - self.center_x
            heart_relative_y = new_y - self.center_y
            new_distance_from_center = abs(heart_relative_x) + abs(heart_relative_y)  # Manhattan distance
            
            # Only accept this step if it maintains or increases distance from center
            if new_distance_from_center >= prev_distance_from_center or step < 3:  # Allow first few steps
                current_x = new_x
                current_y = new_y
                current_angle = test_angle
                prev_distance_from_center = new_distance_from_center
            else:
                # Direction would take us back toward center, adjust angle to move outward
                # Force direction to be more outward-pointing
                center_to_current_angle = math.atan2(
                    current_y - self.center_y, 
                    current_x - self.center_x
                )
                # Bias angle toward outward direction
                current_angle = center_to_current_angle + random.uniform(-0.5, 0.5)
                
                # Step with corrected angle
                current_x += math.cos(current_angle) * step_size_base
                current_y += math.sin(current_angle) * step_size_base
            
            # Add subtle organic curves while maintaining outward flow
            curve_offset_x = math.sin(step * 0.1) * 3
            curve_offset_y = math.cos(step * 0.08) * 3
            
            final_x = current_x + curve_offset_x
            final_y = current_y + curve_offset_y
            
            # Keep within screen bounds
            final_x = max(15, min(self.width - 15, final_x))
            final_y = max(15, min(self.height - 15, final_y))
            
            points.append((int(final_x), int(final_y)))
            
            # Stop if we reach screen edges
            if (final_x <= 20 or final_x >= self.width - 20 or 
                final_y <= 20 or final_y >= self.height - 20):
                break
        
        return points
    
    def initialize_dynamic_arterial_system(self):
        """Initialize the dynamic arterial system with minimal initial paths."""
        # Start with just 2-3 initial arteries - organic growth over time
        initial_count = 2
        
        for i in range(initial_count):
            angle = (2 * math.pi * i) / initial_count + random.uniform(-0.5, 0.5)
            path = self.create_dynamic_artery_path(angle)
            
            if len(path) > 5:
                artery_id = self.next_artery_id
                self.next_artery_id += 1
                
                # Get varied color for this artery
                artery_color = self.get_varied_artery_color(artery_id)
                artery_color = self.add_color_variation(artery_color, 0.1)  # Slight random variation
                
                self.dynamic_arteries[artery_id] = {
                    'path': path,
                    'usage_count': 0,
                    'max_usage': random.randint(2, 5),  # Shorter lifespan for faster turnover
                    'particles': [],
                    'color': artery_color  # Store unique color for this artery
                }
    
    def create_new_particle(self) -> dict:
        """Create a new energy particle."""
        particle_id = self.next_particle_id
        self.next_particle_id += 1
        
        return {
            'id': particle_id,
            'artery_id': None,  # Will be assigned when path is created or found
            'position': 0,
            'speed': random.uniform(0.3, 0.8),
            'brightness': random.uniform(0.6, 1.0),
            'is_pathfinder': False,  # True if this particle creates new paths
            'path_being_created': []  # For pathfinder particles
        }
    
    def initialize_dynamic_particles(self):
        """Initialize particle system with gradual spawning."""
        self.energy_particles = []
        self.dormant_particles = []
        
        # Start with just a few active particles
        initial_active = 6
        
        # Create all particles but most start dormant
        for i in range(self.base_particle_count):
            particle = self.create_new_particle()
            
            if i < initial_active:
                # Make initial particles active
                available_arteries = [aid for aid, artery in self.dynamic_arteries.items() 
                                    if artery['usage_count'] < artery['max_usage']]
                
                if available_arteries:
                    artery_id = random.choice(available_arteries)
                    particle['artery_id'] = artery_id
                    self.dynamic_arteries[artery_id]['particles'].append(particle)
                    self.dynamic_arteries[artery_id]['usage_count'] += 1
                else:
                    # Make it a pathfinder if no arteries available
                    particle['is_pathfinder'] = True
                    self.particles_needing_paths.append(particle)
                
                self.energy_particles.append(particle)
            else:
                # Keep remaining particles dormant for gradual spawning
                self.dormant_particles.append(particle)
    
    def get_heart_texture_color(self, x: int, y: int, base_color: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
        """Generate textured heart color using noise functions."""
        # Distance from center for radial effects
        dx = x - self.center_x
        dy = y - self.center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Multi-frequency noise for organic texture
        noise1 = math.sin(x * 0.02 + t * 0.5) * math.cos(y * 0.02 + t * 0.3)
        noise2 = math.sin(x * 0.008 + t * 0.2) * math.cos(y * 0.01 + t * 0.4)
        noise3 = math.sin(distance * 0.1 + t * 0.6) * 0.3
        
        # Combine noise for texture variation
        texture_factor = (noise1 * 0.4 + noise2 * 0.3 + noise3 * 0.3) * 0.3 + 1.0
        
        # Apply texture to base color
        r = int(base_color[0] * texture_factor)
        g = int(base_color[1] * texture_factor)
        b = int(base_color[2] * texture_factor)
        
        # Clamp values
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    
    def get_varied_artery_color(self, artery_id: int) -> Tuple[int, int, int]:
        """Get a consistent color variation for an artery based on its ID."""
        # Use artery ID to select consistent color variant
        color_index = artery_id % len(self.artery_color_variants)
        return self.artery_color_variants[color_index]
    
    def get_varied_energy_color(self, particle_id: int, artery_id: int) -> Tuple[int, int, int]:
        """Get a varied energy color based on particle and artery properties."""
        # Combine particle and artery ID for color selection
        color_seed = (particle_id + artery_id * 3) % len(self.energy_color_variants)
        return self.energy_color_variants[color_seed]
    
    def add_color_variation(self, base_color: Tuple[int, int, int], variation_factor: float = 0.15) -> Tuple[int, int, int]:
        """Add slight random variation to a color for organic feel."""
        r, g, b = base_color
        
        # Add random variation within bounds
        r_var = r + random.randint(-int(r * variation_factor), int(r * variation_factor))
        g_var = g + random.randint(-int(g * variation_factor), int(g * variation_factor))
        b_var = b + random.randint(-int(b * variation_factor), int(b * variation_factor))
        
        # Clamp values to valid range
        r_var = max(0, min(255, r_var))
        g_var = max(0, min(255, g_var))
        b_var = max(0, min(255, b_var))
        
        return (r_var, g_var, b_var)
    
    def get_anatomical_heart_points(self, size: float) -> List[Tuple[int, int]]:
        """Generate anatomical heart shape points (human/pig heart)."""
        points = []
        
        # Anatomical heart shape - more realistic ventricles and atria
        for angle in range(0, 360, 3):  # Higher resolution
            rad = math.radians(angle)
            
            # Base oval shape for main ventricle
            base_x = math.cos(rad) * size * 0.7
            base_y = math.sin(rad) * size * 0.9
            
            # Add anatomical features
            if 0 <= angle <= 120:  # Right atrium bulge
                bulge_factor = 1.2 + 0.3 * math.sin(rad * 2)
                base_x *= bulge_factor
            elif 160 <= angle <= 200:  # Apex pointing down-left
                base_x *= 0.7
                base_y *= 1.2
            elif 240 <= angle <= 300:  # Left atrium
                bulge_factor = 1.1 + 0.2 * math.sin(rad * 1.5)
                base_x *= bulge_factor
                base_y *= 0.9
            
            # Add surface texture variation
            texture_x = base_x + math.sin(angle * 0.1) * size * 0.05
            texture_y = base_y + math.cos(angle * 0.15) * size * 0.03
            
            # Position and bounds check
            x = int(self.center_x + texture_x)
            y = int(self.center_y + texture_y)
            
            if 20 < x < self.width - 20 and 20 < y < self.height - 20:
                points.append((x, y))
        
        return points
    
    def draw_heart_shape(self, t: float, current_size: float):
        """Draw anatomical heart with selective redrawing."""
        # current_size is the actual pixel radius, no need to multiply
        
        # Only redraw if size changed significantly (reduces flicker)
        if abs(current_size - self.prev_heart_size) > 2:
            # Erase previous heart outline if it was smaller
            if self.prev_heart_size > 0 and self.prev_heart_size > current_size:
                prev_points = self.get_anatomical_heart_points(self.prev_heart_size)
                for x, y in prev_points:
                    # Erase with background color
                    self.display.draw_circle((x, y), 8, self.background_green, True, False)
            
            # Draw current heart
            heart_points = self.get_anatomical_heart_points(current_size)
            
            for x, y in heart_points:
                # Get textured color
                texture_color = self.get_heart_texture_color(x, y, self.heart_pink_base, t)
                
                # Draw heart tissue with organic appearance
                for radius in range(2, 10, 2):
                    fade_factor = 1.0 - (radius - 2) / 10.0
                    faded_color = (
                        int(texture_color[0] * fade_factor),
                        int(texture_color[1] * fade_factor),
                        int(texture_color[2] * fade_factor)
                    )
                    self.display.draw_circle((x, y), radius, faded_color, True, False)
            
            self.prev_heart_size = current_size
    

    
    def draw_frame(self, t: float):
        """Draw a single frame with selective redrawing to reduce flicker."""
        try:
            # Natural rhythm variation - heart transitions between resting/active/energetic states
            # This creates a slowly varying rhythm intensity over time
            rhythm_wave = math.sin(t * self.rhythm_variation_speed) * 0.5 + 0.5
            # Rhythm intensity: 0.5 (resting) to 1.0 (energetic)
            rhythm_intensity = 0.5 + rhythm_wave * 0.5
            
            # Calculate heartbeat pulse with natural dual-chamber rhythm
            # Primary contraction (ventricles)
            primary_beat = math.sin(t * self.heart_beat_speed)
            # Secondary pulse (atria) - slightly faster, creates realistic heart rhythm
            secondary_beat = math.sin(t * self.heart_beat_speed * 1.7) * 0.15
            
            # Combine beats: oscillates from -1 to +1, then scale by rhythm intensity
            combined_beat = (primary_beat + secondary_beat) * rhythm_intensity
            
            # Convert to size: oscillates between heart_min_size and heart_max_size
            # When combined_beat = -1: size = min_size
            # When combined_beat = +1: size = max_size
            current_size = self.heart_min_size + (combined_beat * 0.5 + 0.5) * self.heart_amplitude
            
            # Initialize background once
            if not self.background_initialized:
                # Background with subtle texture variation
                bg_variation = math.sin(t * 0.3) * 3
                bg_color = (
                    max(0, self.background_green[0] + int(bg_variation)),
                    max(0, self.background_green[1] + int(bg_variation)),
                    max(0, self.background_green[2] + int(bg_variation))
                )
                self.display.clear_screen(bg_color)
                self.background_initialized = True
            
            # Update dynamic arterial system and particles
            self.update_energy_particles(t)
            
            # Draw pulsing heart with selective redrawing
            self.draw_heart_shape(t, current_size)
            
            # Update display
            self.display.update_display()
            
        except Exception as e:
            print(f"💔 Error drawing frame: {e}")
    
    def manage_dynamic_arteries(self, t: float):
        """Manage the dynamic arterial system with gradual spawning."""
        # Gradual spawning of new particles (like worms emerging over time)
        if (t - self.last_spawn_time > self.spawn_interval and 
            len(self.dormant_particles) > 0 and 
            len(self.energy_particles) < self.base_particle_count):
            
            # Spawn a few particles at a time
            spawn_count = min(self.particles_per_spawn, len(self.dormant_particles))
            
            for _ in range(spawn_count):
                if self.dormant_particles:
                    particle = self.dormant_particles.pop(0)
                    
                    # 30% chance for new particle to be a pathfinder (forge new territory)
                    if random.random() < 0.3 and len(self.dynamic_arteries) < self.max_arteries:
                        particle['is_pathfinder'] = True
                        self.particles_needing_paths.append(particle)
                    else:
                        # Try to assign to existing artery
                        available_arteries = [aid for aid, artery in self.dynamic_arteries.items() 
                                            if artery['usage_count'] < artery['max_usage']]
                        
                        if available_arteries:
                            artery_id = random.choice(available_arteries)
                            particle['artery_id'] = artery_id
                            self.dynamic_arteries[artery_id]['particles'].append(particle)
                            self.dynamic_arteries[artery_id]['usage_count'] += 1
                        else:
                            # No available arteries, make it a pathfinder
                            particle['is_pathfinder'] = True
                            self.particles_needing_paths.append(particle)
                    
                    self.energy_particles.append(particle)
            
            self.last_spawn_time = t
        
        # Remove expired arteries (fade old worm trails)
        expired_arteries = []
        for artery_id, artery_data in self.dynamic_arteries.items():
            if artery_data['usage_count'] >= artery_data['max_usage'] and len(artery_data['particles']) == 0:
                expired_arteries.append(artery_id)
        
        for artery_id in expired_arteries:
# Fading expired artery with color variation
            # Gradually fade the old artery path from its color toward background
            path = self.dynamic_arteries[artery_id]['path']
            artery_color = self.dynamic_arteries[artery_id].get('color', self.artery_base_color)
            for i, (x, y) in enumerate(path):
                # Create fading effect - interpolate from artery color to background color
                fade_progress = 0.7 + (i % 5) * 0.05  # Progress toward background (0.7 to 0.95)
                
                # Interpolate between artery color and background color
                fade_color = (
                    int(artery_color[0] * (1 - fade_progress) + self.background_green[0] * fade_progress),
                    int(artery_color[1] * (1 - fade_progress) + self.background_green[1] * fade_progress),
                    int(artery_color[2] * (1 - fade_progress) + self.background_green[2] * fade_progress)
                )
                self.display.draw_circle((x, y), 4, fade_color, True, False)
            del self.dynamic_arteries[artery_id]
        
        # Create new paths for pathfinder particles (worms forging new territory)
        for particle in self.particles_needing_paths[:]:
            if len(self.dynamic_arteries) < self.max_arteries:
                # Create new artery path that moves away from center
                new_path = self.create_dynamic_artery_path()
                
                if len(new_path) > 8:  # Ensure meaningful path length
                    artery_id = self.next_artery_id
                    self.next_artery_id += 1
                    
                    # Get varied color for this artery
                    artery_color = self.get_varied_artery_color(artery_id)
                    artery_color = self.add_color_variation(artery_color, 0.1)  # Slight random variation
                    
                    self.dynamic_arteries[artery_id] = {
                        'path': new_path,
                        'usage_count': 1,
                        'max_usage': random.randint(3, 6),  # Shorter worm trail lifespan
                        'particles': [particle],
                        'color': artery_color  # Store unique color for this artery
                    }
                    
                    particle['artery_id'] = artery_id
                    particle['is_pathfinder'] = False
                    self.particles_needing_paths.remove(particle)
    
    def update_energy_particles(self, t: float):
        """Update the dynamic energy particle system."""
        # Manage dynamic arteries first
        self.manage_dynamic_arteries(t)
        
        for particle in self.energy_particles:
            if particle['artery_id'] is None or particle['artery_id'] not in self.dynamic_arteries:
                # Particle needs a new path
                if not particle['is_pathfinder'] and particle not in self.particles_needing_paths:
                    particle['is_pathfinder'] = True
                    self.particles_needing_paths.append(particle)
                continue
            
            artery_data = self.dynamic_arteries[particle['artery_id']]
            artery_path = artery_data['path']
            
            if len(artery_path) == 0:
                continue
                
            # Erase old position
            old_pos_idx = int(particle['position'])
            if 0 <= old_pos_idx < len(artery_path):
                old_x, old_y = artery_path[old_pos_idx]
                # Use the artery's specific color for erasing
                artery_color = artery_data.get('color', self.artery_base_color)
                self.display.draw_circle((old_x, old_y), 4, artery_color, True, False)
            
            # Update particle position
            particle['position'] += particle['speed'] * self.energy_flow_speed
            
            # Handle particle reaching end of artery
            if particle['position'] >= len(artery_path) - 1:
                # Remove particle from this artery
                if particle in artery_data['particles']:
                    artery_data['particles'].remove(particle)
                
                # 70% chance to join existing underused path, 30% chance to create new path
                available_arteries = [aid for aid, adata in self.dynamic_arteries.items() 
                                    if adata['usage_count'] < adata['max_usage'] and aid != particle['artery_id']]
                
                if available_arteries and random.random() < 0.7:
                    # Join an existing underused path
                    artery_id = random.choice(available_arteries)
                    particle['artery_id'] = artery_id
                    particle['position'] = 0
                    self.dynamic_arteries[artery_id]['particles'].append(particle)
                    self.dynamic_arteries[artery_id]['usage_count'] += 1
                else:
                    # Create new path - become pathfinder
                    particle['artery_id'] = None
                    particle['position'] = 0
                    particle['is_pathfinder'] = True
                    particle['path_being_created'] = []
                    if particle not in self.particles_needing_paths:
                        self.particles_needing_paths.append(particle)
                
                # Reset particle for new journey
                particle['position'] = 0
                particle['artery_id'] = None
                
                # Try to assign to existing underused artery first
                available_arteries = [aid for aid, artery in self.dynamic_arteries.items() 
                                    if artery['usage_count'] < artery['max_usage'] and len(artery['particles']) < 3]
                
                if available_arteries and random.random() < 0.7:  # 70% chance to follow existing path
                    artery_id = random.choice(available_arteries)
                    particle['artery_id'] = artery_id
                    self.dynamic_arteries[artery_id]['particles'].append(particle)
                    self.dynamic_arteries[artery_id]['usage_count'] += 1
                    print(f"💚 Particle joined existing path {artery_id}")
                else:
                    # Become pathfinder for new route
                    if len(self.dynamic_arteries) < self.max_arteries:
                        particle['is_pathfinder'] = True
                        if particle not in self.particles_needing_paths:
                            self.particles_needing_paths.append(particle)
                            print(f"💚 Particle becoming pathfinder")
                continue
            
            # Draw new position
            pos_idx = int(particle['position'])
            if 0 <= pos_idx < len(artery_path):
                x, y = artery_path[pos_idx]
                
                # Draw the artery path as particle moves (creates/reinforces path)
                artery_color = artery_data.get('color', self.artery_base_color)
                self.display.draw_circle((x, y), 2, artery_color, True, False)
                
                # Energy particle color with pulsing brightness and variation
                base_energy_color = self.get_varied_energy_color(particle['id'], particle['artery_id'])
                pulse_bright = particle['brightness'] * (1.0 + math.sin(t * 3.0 + pos_idx) * 0.3)
                energy_color = (
                    int(base_energy_color[0] * pulse_bright),
                    int(base_energy_color[1] * pulse_bright),
                    int(base_energy_color[2] * pulse_bright)
                )
                
                # Draw energy particle with glow effect
                for radius in range(1, 4):
                    glow_factor = 1.0 - radius * 0.3
                    glow_color = (
                        int(energy_color[0] * glow_factor),
                        int(energy_color[1] * glow_factor),
                        int(energy_color[2] * glow_factor)
                    )
                    self.display.draw_circle((x, y), radius, glow_color, True, False)
    
    def show_startup_message(self):
        """Show organic startup message."""
        self.display.clear_screen(self.background_green)
        self.display.show_text("💚 HEARTBEAT SCREENSAVER", (400, 400), (100, 150, 80), 32, False)
        self.display.show_text("Organic rhythms for peaceful display", (420, 450), (70, 120, 60), 16, False)
        self.display.show_text("Press Ctrl+C to exit", (500, 500), (60, 100, 50), 14, True)
        time.sleep(3)
    
    def run(self):
        """Run the heartbeat screensaver."""
        print("💚 Heartbeat Screensaver Starting...")
        print("🫀 Organic rhythms and flowing energy...")
        
        # Acquire display
        if not self.display.acquire():
            print("❌ Failed to acquire display manager")
            return False
        
        try:
            # Get actual display dimensions
            info = self.display.get_display_info()
            self.width = info.get('width', 1280)
            self.height = info.get('height', 1024)
            self.center_x = self.width // 2
            self.center_y = self.height // 2
            
            print(f"📺 Display: {self.width}x{self.height}")
            print("🌿 Generating organic arterial network...")
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Initialize dynamic arterial system
            self.initialize_dynamic_arterial_system()
            self.initialize_dynamic_particles()
            
            # Show startup message
            self.show_startup_message()
            
            # Initialize background for selective redrawing
            self.prev_arteries_drawn = False
            self.prev_heart_size = 0
            
            print("💓 Starting heartbeat animation...")
            print("⌨️  Press Ctrl+C to exit")
            
            # Main animation loop
            self.running = True
            frame_count = 0
            fps_start_time = time.time()
            
            while self.running:
                frame_start = time.time()
                t = time.time() - self.start_time
                
                # Draw frame
                self.draw_frame(t)
                frame_count += 1
                
                # Performance monitoring every 5 seconds
                if frame_count % 90 == 0:  # Adjusted for higher FPS
                    runtime = time.time() - self.start_time
                    fps = frame_count / (time.time() - fps_start_time) if frame_count > 0 else 0
                    print(f"💚 Heartbeat: {runtime:.1f}s | FPS: {fps:.1f}")
                
                # Target ~15 FPS for smoother animation (reduce flicker)
                frame_time = time.time() - frame_start
                target_frame_time = 1.0 / 15.0  # 15 FPS
                
                if frame_time < target_frame_time:
                    time.sleep(target_frame_time - frame_time)
            
            # Graceful shutdown
            runtime = time.time() - self.start_time
            avg_fps = frame_count / runtime if runtime > 0 else 0
            
            print(f"\n💚 Heartbeat completed")
            print(f"   Runtime: {runtime:.1f} seconds")
            print(f"   Frames: {frame_count}")
            print(f"   Average FPS: {avg_fps:.1f}")
            print("🌿 Peaceful rhythms complete")
            
            # Goodbye message
            self.display.clear_screen(self.background_green)
            self.display.show_text("💚 PEACEFUL DREAMS", (500, 400), (80, 120, 60), 28, True)
            time.sleep(2)
            
            return True
            
        finally:
            self.display.release()


if __name__ == "__main__":
    screensaver = HeartbeatScreensaver()
    screensaver.run()
